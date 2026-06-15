"""
Project API Routes - All project-related endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import io
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from routes.auth import get_current_user, require_role, require_admin
from modules.upload_module import handle_upload, get_project_files
from modules.code_parser import parse_project, get_parsed_entities
from modules.dependency_mapper import map_dependencies, get_dependency_data
from modules.smell_detector import detect_smells, get_smells
from modules.refactor_engine import suggest_refactorings, get_refactorings, apply_refactor, reject_refactor
from modules.ai_recommender import generate_recommendations, get_suggestions
from modules.graph_generator import generate_graph
from modules.report_generator import generate_json_report, generate_pdf_report
from modules.risk_analyzer import analyze_risk
from modules.refactor_preview import get_preview, get_all_previews
from modules.maintainability_scorer import predict_score
from modules.duplicate_detector import detect_duplicates
from modules.circular_resolver import resolve_circular
from modules.learning_engine import get_learning_stats, predict_acceptance, record_feedback
from database import get_connection

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# ─── Project CRUD ─────────────────────────────────────────

@router.post("/upload")
async def upload_project(file: UploadFile = File(...), current_user: dict = Depends(require_role(["developer"]))):
    """Upload a ZIP file and create a new project."""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are accepted")
    
    contents = await file.read()
    try:
        result = handle_upload(contents, file.filename, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return result


@router.get("/")
def list_projects(current_user: dict = Depends(get_current_user)):
    """List all projects based on user role."""
    conn = get_connection()
    if current_user.get("role") in ["admin", "reviewer"]:
        projects = conn.execute("SELECT p.*, u.name as owner_name FROM projects p JOIN users u ON p.user_id = u.id ORDER BY p.upload_date DESC").fetchall()
    else:
        projects = conn.execute(
            "SELECT * FROM projects WHERE user_id = ? ORDER BY upload_date DESC",
            (current_user["user_id"],)
        ).fetchall()
    conn.close()
    return [dict(p) for p in projects]


@router.get("/{project_id}")
def get_project(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get project details."""
    conn = get_connection()
    if current_user.get("role") in ["admin", "reviewer"]:
        project = conn.execute("SELECT p.*, u.name as owner_name FROM projects p JOIN users u ON p.user_id = u.id WHERE p.id = ?", (project_id,)).fetchone()
    else:
        project = conn.execute("SELECT * FROM projects WHERE id = ? AND user_id = ?",
                               (project_id, current_user["user_id"])).fetchone()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    files = conn.execute("SELECT id, file_name, file_path, language, loc FROM files WHERE project_id = ?",
                         (project_id,)).fetchall()
    smells_count = conn.execute("SELECT COUNT(*) as count FROM code_smells WHERE project_id = ?",
                                (project_id,)).fetchone()["count"]
    refactor_count = conn.execute("SELECT COUNT(*) as count FROM refactoring_history WHERE project_id = ?",
                                  (project_id,)).fetchone()["count"]
    conn.close()
    
    return {
        **dict(project),
        "files": [dict(f) for f in files],
        "smell_count": smells_count,
        "refactor_count": refactor_count
    }


@router.delete("/{project_id}")
def delete_project(project_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a project and all associated data."""
    conn = get_connection()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check permissions
    if current_user.get("role") != "admin" and project["user_id"] != current_user["user_id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    
    if current_user.get("role") == "admin":
        conn.execute(
            "INSERT INTO admin_activity_log (admin_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
            (current_user["user_id"], "delete_project", "project", project_id, f"Deleted project: {project['project_name']}")
        )
    
    conn.commit()
    conn.close()
    return {"message": "Project deleted successfully"}


# ─── Analysis Pipeline ─────────────────────────────────────

@router.post("/{project_id}/analyze")
def full_analysis(project_id: int, current_user: dict = Depends(require_role(["developer"]))):
    """Run full analysis pipeline: parse → dependencies → smells → refactor → AI."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    
    parse_result = parse_project(project_id)
    dep_result = map_dependencies(project_id)
    smell_result = detect_smells(project_id)
    refactor_result = suggest_refactorings(project_id)
    ai_result = generate_recommendations(project_id)
    score_result = predict_score(project_id)
    
    # Save the quality score to the projects table
    conn = get_connection()
    conn.execute(
        "UPDATE projects SET quality_score = ? WHERE id = ?",
        (score_result["score"], project_id)
    )
    conn.commit()
    conn.close()
    
    return {
        "parsing": parse_result,
        "dependencies": {"total": dep_result["total_dependencies"], "circular": len(dep_result["circular_dependencies"])},
        "smells": {"total": smell_result["total_smells"], "by_severity": smell_result["by_severity"]},
        "refactorings": len(refactor_result),
        "ai_suggestions": ai_result["total_suggestions"],
        "maintainability_score": score_result["score"],
        "grade": score_result["grade"]
    }


@router.get("/{project_id}/parse")
def parse(project_id: int, current_user: dict = Depends(get_current_user)):
    """Parse project source code."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return parse_project(project_id)


@router.get("/{project_id}/entities")
def get_entities(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get parsed entities (functions, classes, imports)."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_parsed_entities(project_id)


# ─── Dependencies ─────────────────────────────────────────

@router.get("/{project_id}/dependencies")
def dependencies(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get dependency graph data."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_dependency_data(project_id)


@router.get("/{project_id}/dependencies/graph")
def dep_graph(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get D3-compatible dependency graph."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return generate_graph(project_id)


@router.get("/{project_id}/circular")
def circular(project_id: int, current_user: dict = Depends(get_current_user)):
    """Detect and resolve circular dependencies."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return resolve_circular(project_id)


# ─── Code Smells ──────────────────────────────────────────

@router.get("/{project_id}/smells")
def smells(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get code smells."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_smells(project_id)


@router.get("/{project_id}/duplicates")
def duplicates(project_id: int, current_user: dict = Depends(get_current_user)):
    """Detect smart duplicates across files."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return detect_duplicates(project_id)


# ─── Refactoring ──────────────────────────────────────────

@router.get("/{project_id}/refactorings")
def refactorings(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get refactoring suggestions."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_refactorings(project_id)


@router.post("/{project_id}/refactor/{refactor_id}/apply")
def apply(project_id: int, refactor_id: int, current_user: dict = Depends(get_current_user)):
    """Apply a refactoring."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return apply_refactor(refactor_id)


@router.post("/{project_id}/refactor/{refactor_id}/reject")
def reject(project_id: int, refactor_id: int, current_user: dict = Depends(get_current_user)):
    """Reject a refactoring."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return reject_refactor(refactor_id)


@router.get("/{project_id}/refactor/{refactor_id}/preview")
def preview(project_id: int, refactor_id: int, current_user: dict = Depends(get_current_user)):
    """Get before/after preview of a refactoring."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_preview(refactor_id)


@router.get("/{project_id}/previews")
def all_previews(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get all refactoring previews."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_all_previews(project_id)


# ─── Risk Analysis ────────────────────────────────────────

@router.get("/{project_id}/risk")
def risk(project_id: int, current_user: dict = Depends(get_current_user)):
    """Analyze risk of all refactorings."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return analyze_risk(project_id)


@router.get("/{project_id}/risk/{refactor_id}")
def risk_single(project_id: int, refactor_id: int, current_user: dict = Depends(get_current_user)):
    """Analyze risk of a specific refactoring."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return analyze_risk(project_id, refactor_id)


# ─── AI Recommendations ──────────────────────────────────

@router.get("/{project_id}/recommendations")
def recommendations(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get AI recommendations."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return get_suggestions(project_id)


@router.get("/{project_id}/maintainability")
def maintainability(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get detailed maintainability score."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return predict_score(project_id)


# ─── Learning Engine ─────────────────────────────────────

@router.get("/learning/stats")
def learning_stats(current_user: dict = Depends(get_current_user)):
    """Get learning engine statistics."""
    return get_learning_stats()


@router.get("/learning/predict/{refactor_type}")
def learning_predict(refactor_type: str, current_user: dict = Depends(get_current_user)):
    """Predict acceptance of a refactor type."""
    return predict_acceptance(refactor_type)


# ─── Reports ─────────────────────────────────────────────

@router.get("/{project_id}/report/json")
def report_json(project_id: int, current_user: dict = Depends(get_current_user)):
    """Generate JSON report."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    return generate_json_report(project_id)


@router.get("/{project_id}/report/pdf")
def report_pdf(project_id: int, current_user: dict = Depends(get_current_user)):
    """Generate and download PDF report."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    pdf_bytes = generate_pdf_report(project_id)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_project_{project_id}.pdf"}
    )


# ─── Helpers ──────────────────────────────────────────────

def _verify_project(project_id: int, user_id: int, role: str = "developer"):
    conn = get_connection()
    if role in ["admin", "reviewer"]:
        project = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    else:
        project = conn.execute("SELECT id FROM projects WHERE id = ? AND user_id = ?",
                               (project_id, user_id)).fetchone()
    conn.close()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


# ─── Review Comments ──────────────────────────────────────

class ReviewComment(BaseModel):
    comment: str

@router.get("/{project_id}/comments")
def get_comments(project_id: int, current_user: dict = Depends(get_current_user)):
    """Get review comments for a project."""
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    conn = get_connection()
    comments = conn.execute(
        """SELECT c.id, c.comment, c.created_at, u.name as user_name, u.role as user_role
           FROM review_comments c JOIN users u ON c.user_id = u.id
           WHERE c.project_id = ? ORDER BY c.created_at DESC""",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(c) for c in comments]

@router.post("/{project_id}/comments")
def add_comment(project_id: int, req: ReviewComment, current_user: dict = Depends(require_role(["admin", "reviewer"]))):
    """Add a review comment. Only Admins and Reviewers."""
    # Already protected by role dependency, but verify project exists
    _verify_project(project_id, current_user["user_id"], current_user.get("role"))
    conn = get_connection()
    conn.execute(
        "INSERT INTO review_comments (project_id, user_id, comment) VALUES (?, ?, ?)",
        (project_id, current_user["user_id"], req.comment)
    )
    conn.commit()
    conn.close() 
    return {"message": "Comment added successfully"}
