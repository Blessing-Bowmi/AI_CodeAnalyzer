"""
Automated Refactoring Engine.
Performs: Rename variables, extract method, remove unused code,
simplify conditions, break long functions, fix duplicate logic.
"""

import ast
import re
import textwrap
from database import get_connection


def suggest_refactorings(project_id: int) -> list:
    """Analyze project and suggest refactorings based on detected smells."""
    conn = get_connection()
    try:
        smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
        files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
        
        # Clear previous refactoring suggestions
        conn.execute("DELETE FROM refactoring_history WHERE project_id = ? AND status = 'suggested'", (project_id,))
        
        refactorings = []
        file_map = {dict(f)["file_name"]: dict(f) for f in files}
        
        for smell_row in smells:
            smell = dict(smell_row)
            file_data = file_map.get(smell["file_name"], {})
            content = file_data.get("content", "")
            
            if not content:
                continue
            
            refactor = None
            
            if smell["smell_type"] == "Long Function":
                refactor = _suggest_extract_method(content, smell)
            elif smell["smell_type"] == "Dead Code":
                refactor = _suggest_remove_unused(content, smell)
            elif smell["smell_type"] == "Too Many Parameters":
                refactor = _suggest_param_object(content, smell)
            elif smell["smell_type"] == "Deep Nesting":
                refactor = _suggest_simplify_conditions(content, smell)
            elif smell["smell_type"] == "Duplicate Code":
                refactor = _suggest_extract_duplicate(content, smell)
            elif smell["smell_type"] == "Large Class":
                refactor = _suggest_split_class(content, smell)
            
            if refactor:
                conn.execute(
                    "INSERT INTO refactoring_history (project_id, refactor_type, description, file_name, before_code, after_code, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (project_id, refactor["type"], refactor["description"],
                     smell["file_name"], refactor["before"], refactor["after"], "suggested")
                )
                refactorings.append(refactor)
        
        # Additional: rename poorly named variables
        for file_row in files:
            file_dict = dict(file_row)
            if file_dict.get("language") == "python":
                rename_suggestions = _suggest_rename_variables(file_dict["content"], file_dict["file_name"])
                for r in rename_suggestions:
                    conn.execute(
                        "INSERT INTO refactoring_history (project_id, refactor_type, description, file_name, before_code, after_code, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (project_id, r["type"], r["description"], file_dict["file_name"], r["before"], r["after"], "suggested")
                    )
                refactorings.extend(rename_suggestions)
        
        conn.commit()
    finally:
        conn.close()
    
    return refactorings


def _suggest_extract_method(content: str, smell: dict) -> dict:
    """Suggest extracting a long function into smaller ones."""
    line_num = smell.get("line", 0)
    lines = content.splitlines()
    
    # Find the function
    func_name = ""
    match = re.search(r"Function '(\w+)'", smell["description"])
    if match:
        func_name = match.group(1)
    
    # Get function body
    start = max(0, line_num - 1)
    func_lines = []
    indent_base = 0
    for i in range(start, min(start + 60, len(lines))):
        if i == start:
            indent_base = len(lines[i]) - len(lines[i].lstrip())
        func_lines.append(lines[i])
        if i > start and lines[i].strip() and (len(lines[i]) - len(lines[i].lstrip())) <= indent_base:
            break
    
    before = "\n".join(func_lines[:15]) + "\n    # ... (truncated)"
    
    # Suggest split
    after = f"""def {func_name}_part1(...):
    \"\"\"First part of {func_name} logic.\"\"\"
    # Lines 1-20 of original function
    pass

def {func_name}_part2(...):
    \"\"\"Second part of {func_name} logic.\"\"\"
    # Lines 21-40 of original function
    pass

def {func_name}(...):
    \"\"\"Refactored to delegate to smaller functions.\"\"\"
    result1 = {func_name}_part1(...)
    result2 = {func_name}_part2(...)
    return result2"""
    
    return {
        "type": "Extract Method",
        "description": f"Break '{func_name}' into smaller focused functions",
        "before": before,
        "after": after,
        "file_name": smell["file_name"]
    }


def _suggest_remove_unused(content: str, smell: dict) -> dict:
    """Suggest removing dead/unused code."""
    line_num = smell.get("line", 0)
    lines = content.splitlines()
    
    before_line = lines[line_num - 1] if line_num <= len(lines) else ""
    
    return {
        "type": "Remove Unused Code",
        "description": smell["description"],
        "before": before_line.strip(),
        "after": f"# Removed: {before_line.strip()}",
        "file_name": smell["file_name"]
    }


def _suggest_param_object(content: str, smell: dict) -> dict:
    """Suggest using a parameter object / dataclass."""
    func_name = ""
    match = re.search(r"Function '(\w+)'", smell["description"])
    if match:
        func_name = match.group(1)
    
    before = f"def {func_name}(param1, param2, param3, param4, param5, ...):"
    after = f"""from dataclasses import dataclass

@dataclass
class {func_name.title()}Config:
    param1: str
    param2: int
    param3: float
    param4: bool
    param5: str

def {func_name}(config: {func_name.title()}Config):
    # Access params via config.param1, config.param2, etc."""
    
    return {
        "type": "Introduce Parameter Object",
        "description": f"Group parameters of '{func_name}' into a dataclass",
        "before": before,
        "after": after,
        "file_name": smell["file_name"]
    }


def _suggest_simplify_conditions(content: str, smell: dict) -> dict:
    """Suggest guard clauses for deep nesting."""
    line_num = smell.get("line", 0)
    
    before = """def process(data):
    if data:
        if data.valid:
            if data.ready:
                if data.approved:
                    # deep logic
                    pass"""
    
    after = """def process(data):
    if not data:
        return
    if not data.valid:
        return
    if not data.ready:
        return
    if not data.approved:
        return
    # Clean, flat logic
    pass"""
    
    return {
        "type": "Simplify Conditions",
        "description": f"Replace deep nesting at line {line_num} with guard clauses",
        "before": before,
        "after": after,
        "file_name": smell["file_name"]
    }


def _suggest_extract_duplicate(content: str, smell: dict) -> dict:
    """Suggest extracting duplicate code into shared function."""
    return {
        "type": "Extract Duplicate Logic",
        "description": smell["description"],
        "before": "# Duplicate code in multiple files",
        "after": """# utils.py
def shared_logic(...):
    \"\"\"Extracted common logic.\"\"\"
    pass

# file1.py & file2.py
from utils import shared_logic
result = shared_logic(...)""",
        "file_name": smell["file_name"]
    }


def _suggest_split_class(content: str, smell: dict) -> dict:
    """Suggest splitting a large class."""
    class_name = ""
    match = re.search(r"Class '(\w+)'", smell["description"])
    if match:
        class_name = match.group(1)
    
    return {
        "type": "Split Class",
        "description": f"Split '{class_name}' into focused classes (SRP)",
        "before": f"class {class_name}:  # Too many methods",
        "after": f"""class {class_name}Core:
    \"\"\"Core {class_name} logic.\"\"\"
    pass

class {class_name}IO:
    \"\"\"I/O operations for {class_name}.\"\"\"
    pass

class {class_name}:
    def __init__(self):
        self.core = {class_name}Core()
        self.io = {class_name}IO()""",
        "file_name": smell["file_name"]
    }


def _suggest_rename_variables(content: str, file_name: str) -> list:
    """Detect poorly named variables (single letters, non-descriptive)."""
    suggestions = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if len(name) == 1 and name not in ('i', 'j', 'k', 'x', 'y', '_'):
                            suggestions.append({
                                "type": "Rename Variable",
                                "description": f"Variable '{name}' at line {node.lineno} has a non-descriptive name",
                                "before": f"{name} = ...",
                                "after": f"descriptive_name = ...  # Rename '{name}' to something meaningful",
                                "file_name": file_name
                            })
    except SyntaxError:
        pass
    return suggestions


def get_refactorings(project_id: int) -> list:
    """Get all refactoring suggestions/history for a project."""
    conn = get_connection()
    refactors = conn.execute(
        "SELECT * FROM refactoring_history WHERE project_id = ? ORDER BY date DESC",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in refactors]


def apply_refactor(refactor_id: int) -> dict:
    """Mark a refactoring as applied."""
    conn = get_connection()
    conn.execute(
        "UPDATE refactoring_history SET status = 'applied', date = CURRENT_TIMESTAMP WHERE id = ?",
        (refactor_id,)
    )
    
    refactor = conn.execute("SELECT * FROM refactoring_history WHERE id = ?", (refactor_id,)).fetchone()
    
    # Record in learning data
    if refactor:
        conn.execute(
            "INSERT INTO learning_data (refactor_type, was_accepted, context) VALUES (?, 1, ?)",
            (refactor["refactor_type"], refactor["description"])
        )
    
    conn.commit()
    conn.close()
    return {"status": "applied", "id": refactor_id}


def reject_refactor(refactor_id: int) -> dict:
    """Mark a refactoring as rejected."""
    conn = get_connection()
    conn.execute(
        "UPDATE refactoring_history SET status = 'rejected' WHERE id = ?",
        (refactor_id,)
    )
    
    refactor = conn.execute("SELECT * FROM refactoring_history WHERE id = ?", (refactor_id,)).fetchone()
    if refactor:
        conn.execute(
            "INSERT INTO learning_data (refactor_type, was_accepted, context) VALUES (?, 0, ?)",
            (refactor["refactor_type"], refactor["description"])
        )
    
    conn.commit()
    conn.close()
    return {"status": "rejected", "id": refactor_id}
