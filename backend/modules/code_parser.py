"""
Code Parser Module - Parse source code using Python AST.
Extracts classes, functions, imports, variables from Python files.
Also handles basic parsing for other languages via regex fallback.
"""

import ast
import re
from database import get_connection


def parse_project(project_id: int) -> dict:
    """Parse all files in a project and extract entities."""
    conn = get_connection()
    try:
        files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
        
        stats = {"functions": 0, "classes": 0, "imports": 0, "variables": 0}
        
        for file_row in files:
            file_dict = dict(file_row)
            content = file_dict.get("content", "")
            language = file_dict.get("language", "unknown")
            file_id = file_dict["id"]
            
            if not content.strip():
                continue
            
            if language == "python":
                entities = _parse_python(content)
            elif language in ("javascript", "typescript"):
                entities = _parse_javascript(content)
            elif language == "java":
                entities = _parse_java(content)
            else:
                entities = _parse_generic(content)
            
            # Store entities in DB
            for entity in entities:
                conn.execute(
                    "INSERT INTO parsed_entities (file_id, entity_type, name, start_line, end_line, params, details) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (file_id, entity["type"], entity["name"], entity.get("start_line", 0),
                     entity.get("end_line", 0), entity.get("params", ""), entity.get("details", ""))
                )
                stats[entity["type"] + "s"] = stats.get(entity["type"] + "s", 0) + 1
        
        # Update project stats
        conn.execute(
            "UPDATE projects SET total_functions = ?, total_classes = ? WHERE id = ?",
            (stats.get("functions", 0), stats.get("classs", stats.get("classes", 0)), project_id)
        )
        conn.commit()
    finally:
        conn.close()
    
    return stats


def _parse_python(content: str) -> list:
    """Parse Python code using AST."""
    entities = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _parse_generic(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            params = ", ".join(arg.arg for arg in node.args.args)
            entities.append({
                "type": "function",
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno),
                "params": params,
                "details": f"async={isinstance(node, ast.AsyncFunctionDef)}"
            })
        
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            entities.append({
                "type": "class",
                "name": node.name,
                "start_line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno),
                "params": "",
                "details": f"methods={','.join(methods)};bases={','.join(ast.dump(b) for b in node.bases[:3])}"
            })
        
        elif isinstance(node, ast.Import):
            for alias in node.names:
                entities.append({
                    "type": "import",
                    "name": alias.name,
                    "start_line": node.lineno,
                    "end_line": node.lineno,
                    "params": "",
                    "details": f"alias={alias.asname or ''}"
                })
        
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                entities.append({
                    "type": "import",
                    "name": f"{module}.{alias.name}",
                    "start_line": node.lineno,
                    "end_line": node.lineno,
                    "params": "",
                    "details": f"from={module}"
                })
        
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    entities.append({
                        "type": "variable",
                        "name": target.id,
                        "start_line": node.lineno,
                        "end_line": node.lineno,
                        "params": "",
                        "details": ""
                    })
    
    return entities


def _parse_javascript(content: str) -> list:
    """Parse JavaScript/TypeScript using regex patterns."""
    entities = []
    lines = content.splitlines()
    
    # Functions
    func_patterns = [
        r'function\s+(\w+)\s*\(([^)]*)\)',
        r'(const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>',
        r'(const|let|var)\s+(\w+)\s*=\s*function\s*\(([^)]*)\)',
    ]
    for i, line in enumerate(lines, 1):
        for pattern in func_patterns:
            match = re.search(pattern, line)
            if match:
                groups = match.groups()
                name = groups[0] if 'function' in pattern else groups[1]
                params = groups[-1] if len(groups) > 1 else ""
                entities.append({
                    "type": "function", "name": name,
                    "start_line": i, "end_line": i,
                    "params": params.strip(), "details": ""
                })
                break
    
    # Classes
    for i, line in enumerate(lines, 1):
        match = re.search(r'class\s+(\w+)', line)
        if match:
            entities.append({
                "type": "class", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": "", "details": ""
            })
    
    # Imports
    for i, line in enumerate(lines, 1):
        match = re.search(r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]", line)
        if match:
            entities.append({
                "type": "import", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": "", "details": ""
            })
    
    return entities


def _parse_java(content: str) -> list:
    """Parse Java using regex patterns."""
    entities = []
    lines = content.splitlines()
    
    for i, line in enumerate(lines, 1):
        # Methods
        match = re.search(r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+)\s+(\w+)\s*\(([^)]*)\)', line)
        if match and match.group(1) not in ('if', 'for', 'while', 'switch', 'catch'):
            entities.append({
                "type": "function", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": match.group(2).strip(), "details": ""
            })
        
        # Classes
        match = re.search(r'(?:public\s+)?class\s+(\w+)', line)
        if match:
            entities.append({
                "type": "class", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": "", "details": ""
            })
        
        # Imports
        match = re.search(r'import\s+([\w.]+)', line)
        if match:
            entities.append({
                "type": "import", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": "", "details": ""
            })
    
    return entities


def _parse_generic(content: str) -> list:
    """Generic parser using regex for any language."""
    entities = []
    lines = content.splitlines()
    
    for i, line in enumerate(lines, 1):
        # Generic function detection
        match = re.search(r'(?:def|func|function|fn)\s+(\w+)\s*\(([^)]*)\)', line)
        if match:
            entities.append({
                "type": "function", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": match.group(2).strip(), "details": ""
            })
        
        # Generic class detection
        match = re.search(r'class\s+(\w+)', line)
        if match:
            entities.append({
                "type": "class", "name": match.group(1),
                "start_line": i, "end_line": i,
                "params": "", "details": ""
            })
    
    return entities


def get_parsed_entities(project_id: int) -> list:
    """Get all parsed entities for a project."""
    conn = get_connection()
    entities = conn.execute("""
        SELECT pe.*, f.file_name, f.file_path 
        FROM parsed_entities pe
        JOIN files f ON pe.file_id = f.id
        WHERE f.project_id = ?
        ORDER BY f.file_name, pe.start_line
    """, (project_id,)).fetchall()
    conn.close()
    return [dict(e) for e in entities]
