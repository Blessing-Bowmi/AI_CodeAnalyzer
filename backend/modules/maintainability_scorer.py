"""
Maintainability Score Predictor (Innovative - Viva).
Gives score (0-100) based on Complexity, Duplication, Length, Coupling.
"""

import ast
import math
from database import get_connection


def predict_score(project_id: int) -> dict:
    """Calculate detailed maintainability score with breakdown."""
    conn = get_connection()
    files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
    smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
    deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    
    file_list = [dict(f) for f in files]
    smell_list = [dict(s) for s in smells]
    dep_list = [dict(d) for d in deps]
    
    if not file_list:
        return {"score": 100, "grade": "A+", "breakdown": {}, "details": []}
    
    # 1. Complexity Score (0-25)
    complexity_score = _score_complexity(file_list)
    
    # 2. Duplication Score (0-25)
    duplication_score = _score_duplication(smell_list)
    
    # 3. Length Score (0-25)
    length_score = _score_length(file_list, smell_list)
    
    # 4. Coupling Score (0-25)
    coupling_score = _score_coupling(dep_list, file_list)
    
    total = complexity_score + duplication_score + length_score + coupling_score
    
    breakdown = {
        "complexity": {"score": complexity_score, "max": 25, "description": "Code complexity and nesting depth"},
        "duplication": {"score": duplication_score, "max": 25, "description": "Code duplication across files"},
        "length": {"score": length_score, "max": 25, "description": "Function and file length metrics"},
        "coupling": {"score": coupling_score, "max": 25, "description": "Module coupling and dependencies"},
    }
    
    # Detailed per-file scores
    file_details = []
    for f in file_list:
        file_smells = [s for s in smell_list if s["file_name"] == f["file_name"]]
        file_deps = [d for d in dep_list if f["file_path"] in d.get("source", "")]
        loc = f.get("loc", 0)
        
        file_score = 100
        file_score -= len(file_smells) * 5
        file_score -= max(0, loc - 200) * 0.1
        file_score -= max(0, len(file_deps) - 5) * 3
        file_score = max(0, min(100, file_score))
        
        file_details.append({
            "file": f["file_name"],
            "score": round(file_score, 1),
            "loc": loc,
            "smells": len(file_smells),
            "deps": len(file_deps)
        })
    
    file_details.sort(key=lambda x: x["score"])
    
    return {
        "score": round(total, 1),
        "grade": _to_grade(total),
        "breakdown": breakdown,
        "file_details": file_details,
        "recommendations": _generate_improvement_tips(breakdown)
    }


def _score_complexity(files: list) -> float:
    """Score based on cyclomatic complexity and nesting."""
    score = 25.0
    total_complexity = 0
    
    for f in files:
        content = f.get("content", "")
        if f.get("language") == "python" and content:
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.Try,
                                        ast.ExceptHandler, ast.With)):
                        total_complexity += 1
            except SyntaxError:
                pass
    
    avg_complexity = total_complexity / max(len(files), 1)
    score -= min(25, avg_complexity * 1.5)
    return max(0, round(score, 1))


def _score_duplication(smells: list) -> float:
    """Score based on duplicate code detection."""
    score = 25.0
    dup_count = len([s for s in smells if s["smell_type"] == "Duplicate Code"])
    score -= min(25, dup_count * 4)
    return max(0, round(score, 1))


def _score_length(files: list, smells: list) -> float:
    """Score based on file and function lengths."""
    score = 25.0
    
    # Penalize long files
    long_files = [f for f in files if f.get("loc", 0) > 300]
    score -= min(10, len(long_files) * 3)
    
    # Penalize long functions
    long_fns = [s for s in smells if s["smell_type"] == "Long Function"]
    score -= min(15, len(long_fns) * 3)
    
    return max(0, round(score, 1))


def _score_coupling(deps: list, files: list) -> float:
    """Score based on coupling between modules."""
    score = 25.0
    num_files = max(len(files), 1)
    
    # High dependency ratio
    dep_ratio = len(deps) / num_files
    if dep_ratio > 10:
        score -= 15
    elif dep_ratio > 5:
        score -= 8
    elif dep_ratio > 3:
        score -= 3
    
    # Check for any node with very high coupling
    dep_counts = {}
    for d in deps:
        src = d.get("source", "")
        dep_counts[src] = dep_counts.get(src, 0) + 1
    
    high_coupling = [v for v in dep_counts.values() if v > 8]
    score -= min(10, len(high_coupling) * 5)
    
    return max(0, round(score, 1))


def _to_grade(score: float) -> str:
    if score >= 90: return "A+"
    elif score >= 80: return "A"
    elif score >= 70: return "B"
    elif score >= 60: return "C"
    elif score >= 50: return "D"
    else: return "F"


def _generate_improvement_tips(breakdown: dict) -> list:
    tips = []
    for category, data in breakdown.items():
        ratio = data["score"] / data["max"]
        if ratio < 0.5:
            tips.append(f"🔴 {category.title()} needs significant improvement ({data['score']}/{data['max']})")
        elif ratio < 0.75:
            tips.append(f"🟡 {category.title()} could be improved ({data['score']}/{data['max']})")
        else:
            tips.append(f"🟢 {category.title()} is healthy ({data['score']}/{data['max']})")
    return tips
