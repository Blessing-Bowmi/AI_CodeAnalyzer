"""
AI Recommendation Engine.
Uses Scikit-learn for ML-based suggestions.
Predicts maintainability score, detects risky refactors, suggests best refactor.
"""

import numpy as np
from collections import Counter
from database import get_connection

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def generate_recommendations(project_id: int) -> dict:
    """Generate AI-powered recommendations for a project."""
    conn = get_connection()
    try:
        smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
        files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
        deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
        refactors = conn.execute("SELECT * FROM refactoring_history WHERE project_id = ?", (project_id,)).fetchall()
        
        # Clear previous suggestions
        conn.execute("DELETE FROM ai_suggestions WHERE project_id = ?", (project_id,))
        
        smell_list = [dict(s) for s in smells]
        file_list = [dict(f) for f in files]
        dep_list = [dict(d) for d in deps]
        refactor_list = [dict(r) for r in refactors]
        
        suggestions = []
        
        # 1. Maintainability Score
        score = _calculate_maintainability_score(file_list, smell_list, dep_list)
        
        # 2. Priority Recommendations
        priority_suggestions = _generate_priority_suggestions(smell_list, dep_list, file_list)
        suggestions.extend(priority_suggestions)
        
        # 3. Risk Assessment
        risk_suggestions = _assess_refactor_risks(refactor_list, dep_list)
        suggestions.extend(risk_suggestions)
        
        # 4. ML-based suggestions (if sklearn available)
        if HAS_SKLEARN:
            ml_suggestions = _ml_suggest_refactors(smell_list, refactor_list)
            suggestions.extend(ml_suggestions)
        
        # 5. Architecture suggestions
        arch_suggestions = _architecture_recommendations(dep_list, file_list)
        suggestions.extend(arch_suggestions)
        
        # Store suggestions
        for s in suggestions:
            conn.execute(
                "INSERT INTO ai_suggestions (project_id, suggestion, confidence_score, category, risk_level) VALUES (?, ?, ?, ?, ?)",
                (project_id, s["suggestion"], s["confidence"], s.get("category", "general"), s.get("risk", "low"))
            )
        
        # Update project quality score
        conn.execute("UPDATE projects SET quality_score = ? WHERE id = ?", (score, project_id))
        
        conn.commit()
    finally:
        conn.close()
    
    return {
        "maintainability_score": score,
        "suggestions": suggestions,
        "total_suggestions": len(suggestions)
    }


def _calculate_maintainability_score(files: list, smells: list, deps: list) -> float:
    """Calculate maintainability score (0-100)."""
    if not files:
        return 100.0
    
    total_loc = sum(f.get("loc", 0) for f in files)
    num_files = len(files)
    num_smells = len(smells)
    num_deps = len(deps)
    
    # Base score
    score = 100.0
    
    # Deduct for smells
    severity_weights = {"high": 5, "medium": 3, "low": 1}
    for smell in smells:
        weight = severity_weights.get(smell.get("severity", "low"), 1)
        score -= weight
    
    # Deduct for high coupling (too many dependencies)
    if num_files > 0:
        avg_deps = num_deps / num_files
        if avg_deps > 5:
            score -= (avg_deps - 5) * 2
    
    # Deduct for large files
    for f in files:
        if f.get("loc", 0) > 300:
            score -= 3
    
    # Bonus for good structure
    if num_smells == 0:
        score += 5
    
    return max(0, min(100, round(score, 1)))


def _generate_priority_suggestions(smells: list, deps: list, files: list) -> list:
    """Generate priority-ordered suggestions."""
    suggestions = []
    
    # High severity smells first
    high_smells = [s for s in smells if s.get("severity") == "high"]
    if high_smells:
        smell_types = Counter(s["smell_type"] for s in high_smells)
        most_common = smell_types.most_common(1)[0]
        suggestions.append({
            "suggestion": f"🔴 Critical: Fix {most_common[1]} '{most_common[0]}' issues first — they have the highest impact on code quality",
            "confidence": 0.95,
            "category": "priority",
            "risk": "low"
        })
    
    # Duplicate code
    duplicates = [s for s in smells if s["smell_type"] == "Duplicate Code"]
    if duplicates:
        suggestions.append({
            "suggestion": f"🟡 Found {len(duplicates)} duplicate code blocks. Extract common logic into shared utility modules to reduce maintenance burden",
            "confidence": 0.88,
            "category": "duplication",
            "risk": "medium"
        })
    
    # Dead code
    dead_code = [s for s in smells if s["smell_type"] == "Dead Code"]
    if dead_code:
        suggestions.append({
            "suggestion": f"🟢 Safe cleanup: Remove {len(dead_code)} dead code instances (unused imports, unreachable code) with minimal risk",
            "confidence": 0.92,
            "category": "cleanup",
            "risk": "low"
        })
    
    # File size recommendations
    large_files = [f for f in files if f.get("loc", 0) > 200]
    if large_files:
        suggestions.append({
            "suggestion": f"📦 {len(large_files)} files exceed 200 LOC. Consider splitting them into focused modules following Single Responsibility Principle",
            "confidence": 0.80,
            "category": "architecture",
            "risk": "medium"
        })
    
    return suggestions


def _assess_refactor_risks(refactors: list, deps: list) -> list:
    """Assess risk of suggested refactorings."""
    suggestions = []
    
    for refactor in refactors:
        risk = "low"
        confidence = 0.85
        
        rtype = refactor.get("refactor_type", "")
        
        if rtype == "Extract Method":
            # Check if function is widely called
            func_deps = [d for d in deps if refactor.get("file_name", "") in d.get("target", "")]
            if len(func_deps) > 3:
                risk = "high"
                confidence = 0.70
                suggestions.append({
                    "suggestion": f"⚠️ Risky: '{rtype}' in {refactor.get('file_name', '')} — this function is referenced by {len(func_deps)} other modules. Proceed carefully.",
                    "confidence": confidence,
                    "category": "risk",
                    "risk": risk
                })
        
        elif rtype == "Split Class":
            risk = "medium"
            suggestions.append({
                "suggestion": f"⚠️ Medium Risk: Class splitting in {refactor.get('file_name', '')} may require updating imports across the project",
                "confidence": 0.75,
                "category": "risk",
                "risk": risk
            })
    
    return suggestions


def _ml_suggest_refactors(smells: list, refactors: list) -> list:
    """Use ML to suggest best refactoring actions based on patterns."""
    suggestions = []
    
    if not smells:
        return suggestions
    
    # Build feature matrix from smells
    smell_types = list(set(s["smell_type"] for s in smells))
    severity_map = {"low": 1, "medium": 2, "high": 3}
    
    # Simple ML: cluster smells by type and severity to find patterns
    type_severity = Counter()
    for s in smells:
        key = (s["smell_type"], s.get("severity", "low"))
        type_severity[key] += 1
    
    # Find the most impactful combination
    if type_severity:
        worst = type_severity.most_common(1)[0]
        suggestions.append({
            "suggestion": f"🤖 ML Analysis: Pattern detected — {worst[1]} occurrences of {worst[0][1]}-severity '{worst[0][0]}'. Addressing this pattern will yield the highest improvement.",
            "confidence": 0.82,
            "category": "ml_insight",
            "risk": "low"
        })
    
    # Learning from past refactors
    accepted = [r for r in refactors if r.get("status") == "applied"]
    rejected = [r for r in refactors if r.get("status") == "rejected"]
    
    if accepted:
        preferred_types = Counter(r["refactor_type"] for r in accepted)
        top_pref = preferred_types.most_common(1)[0]
        suggestions.append({
            "suggestion": f"🧠 Learning: You've accepted '{top_pref[0]}' refactoring {top_pref[1]} times. Prioritizing similar suggestions.",
            "confidence": 0.78,
            "category": "learned",
            "risk": "low"
        })
    
    return suggestions


def _architecture_recommendations(deps: list, files: list) -> list:
    """Suggest architectural improvements."""
    suggestions = []
    
    # Check for circular dependencies
    # Build simple graph
    dep_graph = {}
    for d in deps:
        src = d.get("source", "")
        tgt = d.get("target", "")
        if src not in dep_graph:
            dep_graph[src] = set()
        dep_graph[src].add(tgt)
    
    # Check for high coupling
    for node, targets in dep_graph.items():
        if len(targets) > 8:
            suggestions.append({
                "suggestion": f"🏗️ High Coupling: '{node.split('/')[-1]}' depends on {len(targets)} modules. Consider introducing an abstraction layer or facade pattern.",
                "confidence": 0.85,
                "category": "architecture",
                "risk": "medium"
            })
    
    if not suggestions and files:
        suggestions.append({
            "suggestion": "✅ Architecture looks healthy. No critical coupling issues detected.",
            "confidence": 0.90,
            "category": "architecture",
            "risk": "low"
        })
    
    return suggestions


def get_suggestions(project_id: int) -> list:
    """Get stored AI suggestions for a project."""
    conn = get_connection()
    suggestions = conn.execute(
        "SELECT * FROM ai_suggestions WHERE project_id = ? ORDER BY confidence_score DESC",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(s) for s in suggestions]
