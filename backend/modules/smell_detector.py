"""
Code Smell Detection Module.
Detects: Long functions, duplicate code, dead code, large classes,
too many parameters, deep nesting.
"""

import ast
import re
from collections import Counter
from database import get_connection


# Thresholds (Lowered to ensure small demo code triggers the pipeline)
MAX_FUNCTION_LINES = 3
MAX_CLASS_METHODS = 2
MAX_PARAMETERS = 2
MAX_NESTING_DEPTH = 2
DUPLICATE_MIN_LINES = 2


def detect_smells(project_id: int) -> dict:
    """Run all smell detectors on a project."""
    conn = get_connection()
    try:
        files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
        
        # Clear previous smells
        conn.execute("DELETE FROM code_smells WHERE project_id = ?", (project_id,))
        
        all_smells = []
        all_code_blocks = []  # For duplicate detection across files
        
        for file_row in files:
            file_dict = dict(file_row)
            content = file_dict.get("content", "")
            file_name = file_dict.get("file_name", "")
            language = file_dict.get("language", "unknown")
            
            if not content.strip():
                continue
            
            smells = []
            
            if language == "python":
                smells.extend(_detect_long_functions_python(content, file_name))
                smells.extend(_detect_large_classes_python(content, file_name))
                smells.extend(_detect_too_many_params_python(content, file_name))
                smells.extend(_detect_deep_nesting(content, file_name))
                smells.extend(_detect_dead_code_python(content, file_name))
                all_code_blocks.append({"file": file_name, "content": content})
            else:
                smells.extend(_detect_long_functions_generic(content, file_name))
                smells.extend(_detect_deep_nesting(content, file_name))
                smells.extend(_detect_too_many_params_generic(content, file_name))
            
            for smell in smells:
                conn.execute(
                    "INSERT INTO code_smells (project_id, file_name, smell_type, severity, line, description, suggestion) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (project_id, smell["file_name"], smell["smell_type"], smell["severity"],
                     smell.get("line", 0), smell["description"], smell.get("suggestion", ""))
                )
            
            all_smells.extend(smells)
        
        # Cross-file duplicate detection
        dup_smells = _detect_duplicates(all_code_blocks, project_id)
        for smell in dup_smells:
            conn.execute(
                "INSERT INTO code_smells (project_id, file_name, smell_type, severity, line, description, suggestion) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project_id, smell["file_name"], smell["smell_type"], smell["severity"],
                 smell.get("line", 0), smell["description"], smell.get("suggestion", ""))
            )
        all_smells.extend(dup_smells)
        
        conn.commit()
    finally:
        conn.close()
    
    # Summary
    severity_counts = Counter(s["severity"] for s in all_smells)
    type_counts = Counter(s["smell_type"] for s in all_smells)
    
    return {
        "total_smells": len(all_smells),
        "by_severity": dict(severity_counts),
        "by_type": dict(type_counts),
        "smells": all_smells
    }


def _detect_long_functions_python(content: str, file_name: str) -> list:
    smells = []
    lines = content.splitlines()
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if hasattr(node, 'end_lineno') and node.end_lineno is not None:
                    length = node.end_lineno - node.lineno + 1
                else:
                    # Fallback for older python versions
                    start = node.lineno - 1
                    end = start
                    while end < len(lines) and (lines[end].startswith(' ') or lines[end].startswith('\t') or not lines[end].strip() or lines[end].strip().startswith('#') or end == start):
                        end += 1
                    length = end - start
                    
                if length > MAX_FUNCTION_LINES:
                    severity = "high" if length > MAX_FUNCTION_LINES * 2 else "medium"
                    smells.append({
                        "file_name": file_name, "smell_type": "Long Function",
                        "severity": severity, "line": node.lineno,
                        "description": f"Function '{node.name}' is {length} lines long (max: {MAX_FUNCTION_LINES})",
                        "suggestion": f"Break '{node.name}' into smaller functions with single responsibilities"
                    })
    except SyntaxError:
        pass
    return smells


def _detect_large_classes_python(content: str, file_name: str) -> list:
    smells = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if len(methods) > MAX_CLASS_METHODS:
                    smells.append({
                        "file_name": file_name, "smell_type": "Large Class",
                        "severity": "high" if len(methods) > MAX_CLASS_METHODS * 2 else "medium",
                        "line": node.lineno,
                        "description": f"Class '{node.name}' has {len(methods)} methods (max: {MAX_CLASS_METHODS})",
                        "suggestion": f"Consider splitting '{node.name}' using Single Responsibility Principle"
                    })
    except SyntaxError:
        pass
    return smells


def _detect_too_many_params_python(content: str, file_name: str) -> list:
    smells = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                params = [a.arg for a in node.args.args if a.arg != 'self']
                if len(params) > MAX_PARAMETERS:
                    smells.append({
                        "file_name": file_name, "smell_type": "Too Many Parameters",
                        "severity": "medium", "line": node.lineno,
                        "description": f"Function '{node.name}' has {len(params)} parameters (max: {MAX_PARAMETERS})",
                        "suggestion": f"Consider using a config object or dataclass for '{node.name}' parameters"
                    })
    except SyntaxError:
        pass
    return smells


def _detect_deep_nesting(content: str, file_name: str) -> list:
    smells = []
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        if line.strip():
            indent = len(line) - len(line.lstrip())
            indent_level = indent // 4  # Assuming 4-space indent
            if indent_level > MAX_NESTING_DEPTH:
                smells.append({
                    "file_name": file_name, "smell_type": "Deep Nesting",
                    "severity": "medium", "line": i,
                    "description": f"Code at line {i} has nesting depth of {indent_level} (max: {MAX_NESTING_DEPTH})",
                    "suggestion": "Use early returns, guard clauses, or extract nested logic into functions"
                })
    return smells


def _detect_dead_code_python(content: str, file_name: str) -> list:
    """Detect potentially dead code (unreachable after return, unused imports)."""
    smells = []
    try:
        tree = ast.parse(content)
        
        # Check for code after return
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_return = False
                for child in node.body:
                    if found_return:
                        smells.append({
                            "file_name": file_name, "smell_type": "Dead Code",
                            "severity": "low", "line": child.lineno,
                            "description": f"Unreachable code after return in '{node.name}'",
                            "suggestion": "Remove unreachable code after return statement"
                        })
                        break
                    if isinstance(child, ast.Return):
                        found_return = True
        
        # Unused imports (simple check)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    imports.append((name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    imports.append((name, node.lineno))
        
        for name, lineno in imports:
            # Simple check: if name not used elsewhere in code
            usage_count = len(re.findall(r'\b' + re.escape(name) + r'\b', content))
            if usage_count <= 1:  # Only appears in import
                smells.append({
                    "file_name": file_name, "smell_type": "Dead Code",
                    "severity": "low", "line": lineno,
                    "description": f"Unused import: '{name}'",
                    "suggestion": f"Remove unused import '{name}'"
                })
    except SyntaxError:
        pass
    return smells


def _detect_long_functions_generic(content: str, file_name: str) -> list:
    smells = []
    func_pattern = r'(?:def|function|func|fn)\s+(\w+)'
    lines = content.splitlines()
    func_starts = []
    
    for i, line in enumerate(lines, 1):
        match = re.search(func_pattern, line)
        if match:
            func_starts.append((match.group(1), i))
    
    for j, (name, start) in enumerate(func_starts):
        end = func_starts[j + 1][1] - 1 if j + 1 < len(func_starts) else len(lines)
        length = end - start + 1
        if length > MAX_FUNCTION_LINES:
            smells.append({
                "file_name": file_name, "smell_type": "Long Function",
                "severity": "high" if length > MAX_FUNCTION_LINES * 2 else "medium",
                "line": start,
                "description": f"Function '{name}' is approximately {length} lines long",
                "suggestion": f"Break '{name}' into smaller functions"
            })
    return smells


def _detect_too_many_params_generic(content: str, file_name: str) -> list:
    smells = []
    pattern = r'(?:def|function|func|fn)\s+(\w+)\s*\(([^)]*)\)'
    for match in re.finditer(pattern, content):
        params = [p.strip() for p in match.group(2).split(',') if p.strip()]
        if len(params) > MAX_PARAMETERS:
            line = content[:match.start()].count('\n') + 1
            smells.append({
                "file_name": file_name, "smell_type": "Too Many Parameters",
                "severity": "medium", "line": line,
                "description": f"Function '{match.group(1)}' has {len(params)} parameters",
                "suggestion": "Consider grouping parameters into an object"
            })
    return smells


def _detect_duplicates(code_blocks: list, project_id: int) -> list:
    """Detect duplicate code blocks across files."""
    smells = []
    block_hashes = {}
    
    for block in code_blocks:
        lines = block["content"].splitlines()
        for i in range(len(lines) - DUPLICATE_MIN_LINES + 1):
            chunk = "\n".join(lines[i:i + DUPLICATE_MIN_LINES]).strip()
            if not chunk or len(chunk) < 50:
                continue
            
            normalized = re.sub(r'\s+', ' ', chunk)
            if normalized in block_hashes:
                orig = block_hashes[normalized]
                if orig["file"] != block["file"]:
                    smells.append({
                        "file_name": block["file"], "smell_type": "Duplicate Code",
                        "severity": "medium", "line": i + 1,
                        "description": f"Duplicate code block found in '{block['file']}' (also in '{orig['file']}')",
                        "suggestion": "Extract duplicate logic into a shared utility function"
                    })
            else:
                block_hashes[normalized] = {"file": block["file"], "line": i + 1}
    
    return smells


def get_smells(project_id: int) -> list:
    """Get all code smells for a project."""
    conn = get_connection()
    smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    return [dict(s) for s in smells]
