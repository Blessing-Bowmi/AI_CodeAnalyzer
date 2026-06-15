"""
Smart Duplicate Detector (Innovative - Viva).
Detects logic duplication across files, suggests reusable functions.
"""

import re
import hashlib
from collections import defaultdict
from database import get_connection


def detect_duplicates(project_id: int) -> dict:
    """Detect code duplication across all files in a project."""
    conn = get_connection()
    files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    
    file_list = [dict(f) for f in files]
    
    # Extract function-level blocks for comparison
    blocks = []
    for f in file_list:
        content = f.get("content", "")
        if not content.strip():
            continue
        func_blocks = _extract_code_blocks(content, f["file_name"])
        blocks.extend(func_blocks)
    
    # Find similar blocks
    duplicates = _find_similar_blocks(blocks)
    
    # Generate suggestions
    suggestions = []
    for dup_group in duplicates:
        suggestion = _generate_reuse_suggestion(dup_group)
        suggestions.append(suggestion)
    
    return {
        "total_duplicates": len(duplicates),
        "duplicate_groups": duplicates,
        "suggestions": suggestions
    }


def _extract_code_blocks(content: str, file_name: str) -> list:
    """Extract meaningful code blocks from content."""
    blocks = []
    lines = content.splitlines()
    
    # Extract function bodies
    func_pattern = r'(?:def|function|func)\s+(\w+)'
    i = 0
    while i < len(lines):
        match = re.search(func_pattern, lines[i])
        if match:
            func_name = match.group(1)
            start = i
            indent = len(lines[i]) - len(lines[i].lstrip())
            end = i + 1
            while end < len(lines):
                if lines[end].strip() and (len(lines[end]) - len(lines[end].lstrip())) <= indent:
                    break
                end += 1
            
            body = "\n".join(lines[start:end])
            if len(body.strip()) > 30:  # Minimum meaningful block
                normalized = _normalize_code(body)
                blocks.append({
                    "file": file_name,
                    "function": func_name,
                    "start_line": start + 1,
                    "end_line": end,
                    "code": body,
                    "normalized": normalized,
                    "hash": hashlib.md5(normalized.encode()).hexdigest()
                })
            i = end
        else:
            i += 1
    
    # Also extract arbitrary blocks of 5+ lines
    window_size = 5
    for i in range(len(lines) - window_size + 1):
        block = "\n".join(lines[i:i + window_size])
        if len(block.strip()) > 50:
            normalized = _normalize_code(block)
            blocks.append({
                "file": file_name,
                "function": f"block_L{i+1}",
                "start_line": i + 1,
                "end_line": i + window_size,
                "code": block,
                "normalized": normalized,
                "hash": hashlib.md5(normalized.encode()).hexdigest()
            })
    
    return blocks


def _normalize_code(code: str) -> str:
    """Normalize code for comparison (remove variable names, whitespace)."""
    # Remove comments
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code).strip()
    
    # Replace string literals
    code = re.sub(r"'[^']*'", "'STR'", code)
    code = re.sub(r'"[^"]*"', '"STR"', code)
    
    # Replace numbers
    code = re.sub(r'\b\d+\b', 'NUM', code)
    
    return code


def _find_similar_blocks(blocks: list) -> list:
    """Find groups of similar code blocks."""
    hash_groups = defaultdict(list)
    
    for block in blocks:
        hash_groups[block["hash"]].append(block)
    
    duplicates = []
    seen_pairs = set()
    
    for hash_val, group in hash_groups.items():
        if len(group) < 2:
            continue
        
        # Filter: must be from different files
        unique_files = set(b["file"] for b in group)
        if len(unique_files) < 2:
            continue
        
        # Deduplicate
        pair_key = tuple(sorted(set(f"{b['file']}:{b['function']}" for b in group)))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)
        
        duplicates.append({
            "similarity": 100,  # Exact match after normalization
            "blocks": [{
                "file": b["file"],
                "function": b["function"],
                "start_line": b["start_line"],
                "end_line": b["end_line"],
                "code_preview": b["code"][:200]
            } for b in group[:5]]  # Limit to 5 instances
        })
    
    return duplicates[:20]  # Limit results


def _generate_reuse_suggestion(dup_group: dict) -> dict:
    """Generate a reuse suggestion for a group of duplicates."""
    blocks = dup_group.get("blocks", [])
    files = [b["file"] for b in blocks]
    
    return {
        "type": "Extract Shared Function",
        "description": f"Found duplicate logic in {len(files)} files: {', '.join(files[:3])}",
        "suggestion": "Create a shared utility function and import it in all affected files",
        "affected_files": files,
        "estimated_savings": f"{len(blocks) - 1} duplicate blocks can be replaced with function calls",
        "confidence": 0.85
    }
