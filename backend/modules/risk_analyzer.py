"""
Risk Analyzer Module (Innovative - Viva).
Detects dangerous refactoring, warns before applying.
"""

from database import get_connection


def analyze_risk(project_id: int, refactor_id: int = None) -> dict:
    """Analyze risk of refactoring operations."""
    conn = get_connection()
    deps = conn.execute("SELECT * FROM dependencies WHERE project_id = ?", (project_id,)).fetchall()
    smells = conn.execute("SELECT * FROM code_smells WHERE project_id = ?", (project_id,)).fetchall()
    refactors = conn.execute("SELECT * FROM refactoring_history WHERE project_id = ?", (project_id,)).fetchall()
    
    dep_list = [dict(d) for d in deps]
    refactor_list = [dict(r) for r in refactors]
    
    risks = []
    
    target_refactors = refactor_list
    if refactor_id:
        target_refactors = [r for r in refactor_list if r["id"] == refactor_id]
    
    for refactor in target_refactors:
        risk_score = 0
        warnings = []
        
        rtype = refactor.get("refactor_type", "")
        file_name = refactor.get("file_name", "")
        
        # Check how many modules depend on this file
        dependents = [d for d in dep_list if file_name in d.get("target", "")]
        if len(dependents) > 5:
            risk_score += 30
            warnings.append(f"High coupling: {len(dependents)} modules depend on this file")
        elif len(dependents) > 2:
            risk_score += 15
            warnings.append(f"Moderate coupling: {len(dependents)} modules depend on this file")
        
        # Type-based risk
        type_risks = {
            "Extract Method": 20,
            "Split Class": 40,
            "Rename Variable": 10,
            "Remove Unused Code": 5,
            "Simplify Conditions": 15,
            "Extract Duplicate Logic": 25,
            "Introduce Parameter Object": 30,
        }
        risk_score += type_risks.get(rtype, 15)
        
        # Check if file has many smells (fragile code)
        file_smells = [s for s in [dict(s) for s in smells] if s["file_name"] == file_name]
        if len(file_smells) > 5:
            risk_score += 20
            warnings.append(f"File has {len(file_smells)} code smells — highly fragile")
        
        # Determine risk level
        if risk_score >= 60:
            level = "high"
            warnings.append("HIGH RISK: Review carefully before applying")
        elif risk_score >= 30:
            level = "medium"
            warnings.append("MEDIUM RISK: Test thoroughly after applying")
        else:
            level = "low"
            warnings.append("LOW RISK: Safe to apply")
        
        risks.append({
            "refactor_id": refactor.get("id"),
            "refactor_type": rtype,
            "file_name": file_name,
            "risk_score": min(100, risk_score),
            "risk_level": level,
            "warnings": warnings,
            "recommendation": "proceed" if level == "low" else "review" if level == "medium" else "caution"
        })
    
    conn.close()
    return {"risks": risks, "total_analyzed": len(risks)}
