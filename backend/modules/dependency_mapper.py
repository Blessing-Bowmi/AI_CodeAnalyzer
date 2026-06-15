"""
Dependency Mapping Module - Build call graph, detect module & circular dependencies.
Uses NetworkX for graph operations.
"""

import ast
import re
import networkx as nx
from database import get_connection


def map_dependencies(project_id: int) -> dict:
    """Build dependency graph for a project."""
    conn = get_connection()
    try:
        files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
        
        # Clear existing dependencies
        conn.execute("DELETE FROM dependencies WHERE project_id = ?", (project_id,))
        
        graph = nx.DiGraph()
        dependencies = []
        
        for file_row in files:
            file_dict = dict(file_row)
            content = file_dict.get("content", "")
            file_path = file_dict.get("file_path", "")
            language = file_dict.get("language", "unknown")
            
            if not content.strip():
                continue
            
            graph.add_node(file_path)
            
            if language == "python":
                deps = _extract_python_deps(content, file_path)
            elif language in ("javascript", "typescript"):
                deps = _extract_js_deps(content, file_path)
            else:
                deps = _extract_generic_deps(content, file_path)
            
            for dep in deps:
                graph.add_edge(dep["source"], dep["target"])
                dependencies.append(dep)
                conn.execute(
                    "INSERT INTO dependencies (project_id, source, target, type) VALUES (?, ?, ?, ?)",
                    (project_id, dep["source"], dep["target"], dep["type"])
                )
        
        # Detect function-to-function calls
        func_calls = _extract_function_calls(files)
        for call in func_calls:
            conn.execute(
                "INSERT INTO dependencies (project_id, source, target, type) VALUES (?, ?, ?, ?)",
                (project_id, call["source"], call["target"], "function_call")
            )
            dependencies.append(call)
        
        conn.commit()
        
        # Detect circular dependencies
        circular = _detect_circular_deps(graph)
        
    finally:
        conn.close()
    
    return {
        "total_dependencies": len(dependencies),
        "module_dependencies": len([d for d in dependencies if d["type"] == "module"]),
        "function_calls": len([d for d in dependencies if d["type"] == "function_call"]),
        "circular_dependencies": circular,
        "nodes": list(graph.nodes()),
        "edges": [{"source": u, "target": v} for u, v in graph.edges()]
    }


def _extract_python_deps(content: str, file_path: str) -> list:
    """Extract import dependencies from Python code."""
    deps = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.append({"source": file_path, "target": alias.name, "type": "module"})
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                deps.append({"source": file_path, "target": module, "type": "module"})
    except SyntaxError:
        pass
    return deps


def _extract_js_deps(content: str, file_path: str) -> list:
    """Extract import/require dependencies from JS/TS code."""
    deps = []
    patterns = [
        r"import\s+[\s\S]*?from\s+['\"]([^'\"]+)['\"]",
        r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"import\s+['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            deps.append({"source": file_path, "target": match.group(1), "type": "module"})
    return deps


def _extract_generic_deps(content: str, file_path: str) -> list:
    """Extract dependencies using generic patterns."""
    deps = []
    patterns = [
        r'#include\s*[<"]([^>"]+)[>"]',
        r'using\s+([\w.]+)\s*;',
        r'import\s+([\w.]+)',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            deps.append({"source": file_path, "target": match.group(1), "type": "module"})
    return deps


def _extract_function_calls(files) -> list:
    """Extract function-to-function call dependencies."""
    calls = []
    
    # First pass: collect all function definitions
    all_functions = {}
    for file_row in files:
        file_dict = dict(file_row)
        content = file_dict.get("content", "")
        file_path = file_dict.get("file_path", "")
        
        if file_dict.get("language") == "python":
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        all_functions[node.name] = file_path
            except SyntaxError:
                pass
    
    # Second pass: find calls
    for file_row in files:
        file_dict = dict(file_row)
        content = file_dict.get("content", "")
        file_path = file_dict.get("file_path", "")
        
        if file_dict.get("language") == "python":
            try:
                tree = ast.parse(content)
                
                class CallVisitor(ast.NodeVisitor):
                    def __init__(self):
                        self.current_func = None
                        
                    def visit_FunctionDef(self, node):
                        prev_func = self.current_func
                        self.current_func = node.name
                        self.generic_visit(node)
                        self.current_func = prev_func
                        
                    def visit_AsyncFunctionDef(self, node):
                        self.visit_FunctionDef(node)
                        
                    def visit_Call(self, node):
                        if self.current_func:
                            called = None
                            if isinstance(node.func, ast.Name):
                                called = node.func.id
                            elif isinstance(node.func, ast.Attribute):
                                called = node.func.attr
                                
                            if called and called in all_functions:
                                calls.append({
                                    "source": f"{file_path}::{self.current_func}",
                                    "target": f"{all_functions[called]}::{called}",
                                    "type": "function_call"
                                })
                        self.generic_visit(node)

                CallVisitor().visit(tree)
            except SyntaxError:
                pass
    
    return calls


def _detect_circular_deps(graph: nx.DiGraph) -> list:
    """Detect circular dependencies using DFS."""
    cycles = []
    try:
        for cycle in nx.simple_cycles(graph):
            if len(cycle) > 1:
                cycles.append(cycle)
    except Exception:
        pass
    return cycles


def get_dependency_data(project_id: int) -> dict:
    """Get stored dependency data for visualization."""
    conn = get_connection()
    deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    
    dep_list = [dict(d) for d in deps]
    
    nodes = set()
    for d in dep_list:
        nodes.add(d["source"])
        nodes.add(d["target"])
    
    return {
        "nodes": [{"id": n, "label": n.split("/")[-1] if "/" in n else n} for n in nodes],
        "links": [{"source": d["source"], "target": d["target"], "type": d["type"]} for d in dep_list],
        "total": len(dep_list)
    }
