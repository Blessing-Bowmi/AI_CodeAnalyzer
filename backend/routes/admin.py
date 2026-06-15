"""
Admin API Routes - Admin-only endpoints for system management.
User management, system analytics, activity logs.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from routes.auth import require_admin
from database import get_connection

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ─── Models ───────────────────────────────────────────────

class RoleUpdate(BaseModel):
    role: str


# ─── Dashboard ────────────────────────────────────────────

@router.get("/dashboard")
def admin_dashboard(current_user: dict = Depends(require_admin)):
    """Get system-wide admin dashboard stats."""
    conn = get_connection()

    total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
    total_projects = conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()["c"]
    total_files = conn.execute("SELECT COUNT(*) as c FROM files").fetchone()["c"]
    total_smells = conn.execute("SELECT COUNT(*) as c FROM code_smells").fetchone()["c"]
    total_refactors = conn.execute("SELECT COUNT(*) as c FROM refactoring_history").fetchone()["c"]
    total_ai = conn.execute("SELECT COUNT(*) as c FROM ai_suggestions").fetchone()["c"]

    # Role breakdown
    roles = conn.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role").fetchall()
    role_breakdown = {r["role"]: r["count"] for r in roles}

    # Refactoring status breakdown
    ref_status = conn.execute(
        "SELECT status, COUNT(*) as count FROM refactoring_history GROUP BY status"
    ).fetchall()
    refactor_breakdown = {r["status"]: r["count"] for r in ref_status}

    # Smell severity breakdown
    smell_sev = conn.execute(
        "SELECT severity, COUNT(*) as count FROM code_smells GROUP BY severity"
    ).fetchall()
    smell_breakdown = {s["severity"]: s["count"] for s in smell_sev}

    # Avg quality score
    avg_quality = conn.execute(
        "SELECT AVG(quality_score) as avg FROM projects WHERE quality_score > 0"
    ).fetchone()["avg"] or 0

    # Recent projects (last 10)
    recent_projects = conn.execute(
        """SELECT p.id, p.project_name, p.upload_date, p.quality_score, p.total_files,
                  u.name as owner_name, u.email as owner_email
           FROM projects p JOIN users u ON p.user_id = u.id
           ORDER BY p.upload_date DESC LIMIT 10"""
    ).fetchall()

    # Recent users (last 10)
    recent_users = conn.execute(
        "SELECT id, name, email, role, created_at FROM users ORDER BY id DESC LIMIT 10"
    ).fetchall()

    conn.close()

    return {
        "stats": {
            "total_users": total_users,
            "total_projects": total_projects,
            "total_files": total_files,
            "total_smells": total_smells,
            "total_refactors": total_refactors,
            "total_ai_suggestions": total_ai,
            "avg_quality_score": round(avg_quality, 1)
        },
        "role_breakdown": role_breakdown,
        "refactor_breakdown": refactor_breakdown,
        "smell_breakdown": smell_breakdown,
        "recent_projects": [dict(p) for p in recent_projects],
        "recent_users": [dict(u) for u in recent_users]
    }


# ─── User Management ─────────────────────────────────────

@router.get("/users")
def list_users(current_user: dict = Depends(require_admin)):
    """List all registered users."""
    conn = get_connection()
    users = conn.execute(
        """SELECT u.id, u.name, u.email, u.role, u.created_at,
                  COUNT(p.id) as project_count
           FROM users u LEFT JOIN projects p ON u.id = p.user_id
           GROUP BY u.id ORDER BY u.id DESC"""
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]


@router.get("/users/{user_id}")
def get_user_detail(user_id: int, current_user: dict = Depends(require_admin)):
    """Get detailed info about a specific user."""
    conn = get_connection()
    user = conn.execute(
        "SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    projects = conn.execute(
        "SELECT id, project_name, upload_date, quality_score, total_files FROM projects WHERE user_id = ? ORDER BY upload_date DESC",
        (user_id,)
    ).fetchall()

    # Count user's smells and refactorings
    project_ids = [p["id"] for p in projects]
    total_smells = 0
    total_refactors = 0
    if project_ids:
        placeholders = ",".join("?" * len(project_ids))
        total_smells = conn.execute(
            "SELECT COUNT(*) as c FROM code_smells WHERE project_id IN ({})".format(placeholders),
            project_ids
        ).fetchone()["c"]
        total_refactors = conn.execute(
            "SELECT COUNT(*) as c FROM refactoring_history WHERE project_id IN ({})".format(placeholders),
            project_ids
        ).fetchone()["c"]
    conn.close()

    return {
        **dict(user),
        "projects": [dict(p) for p in projects],
        "total_smells": total_smells,
        "total_refactors": total_refactors
    }


@router.put("/users/{user_id}/role")
def update_user_role(user_id: int, req: RoleUpdate, current_user: dict = Depends(require_admin)):
    """Change a user's role."""
    if req.role not in ["developer", "admin", "reviewer"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be: developer, admin, reviewer")
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    conn = get_connection()
    user = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    conn.execute("UPDATE users SET role = ? WHERE id = ?", (req.role, user_id))
    # Log the action
    conn.execute(
        "INSERT INTO admin_activity_log (admin_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
        (current_user["user_id"], "change_role", "user", user_id, "Changed role to {}".format(req.role))
    )
    conn.commit()
    conn.close()
    return {"message": "Role updated to {}".format(req.role), "user_id": user_id}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    """Delete a user and all their data."""
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    conn = get_connection()
    user = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Delete user's projects and cascading data
    conn.execute("DELETE FROM projects WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    # Log the action
    conn.execute(
        "INSERT INTO admin_activity_log (admin_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
        (current_user["user_id"], "delete_user", "user", user_id, "Deleted user: {} ({})".format(user["name"], user["email"]))
    )
    conn.commit()
    conn.close()
    return {"message": "User deleted", "user_id": user_id}


# ─── All Projects (Admin View) ───────────────────────────

@router.get("/projects")
def list_all_projects(current_user: dict = Depends(require_admin)):
    """List ALL projects across the system."""
    conn = get_connection()
    projects = conn.execute(
        """SELECT p.*, u.name as owner_name, u.email as owner_email,
                  (SELECT COUNT(*) FROM code_smells WHERE project_id = p.id) as smell_count,
                  (SELECT COUNT(*) FROM refactoring_history WHERE project_id = p.id) as refactor_count
           FROM projects p JOIN users u ON p.user_id = u.id
           ORDER BY p.upload_date DESC"""
    ).fetchall()
    conn.close()
    return [dict(p) for p in projects]


@router.delete("/projects/{project_id}")
def admin_delete_project(project_id: int, current_user: dict = Depends(require_admin)):
    """Admin delete any project."""
    conn = get_connection()
    project = conn.execute("SELECT id, project_name, user_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.execute(
        "INSERT INTO admin_activity_log (admin_id, action, target_type, target_id, details) VALUES (?, ?, ?, ?, ?)",
        (current_user["user_id"], "delete_project", "project", project_id, "Deleted project: {}".format(project["project_name"]))
    )
    conn.commit()
    conn.close()
    return {"message": "Project deleted by admin"}


# ─── System Analytics ─────────────────────────────────────

@router.get("/analytics")
def system_analytics(current_user: dict = Depends(require_admin)):
    """Get detailed system analytics."""
    conn = get_connection()

    # Smells by type across entire system
    smell_types = conn.execute(
        "SELECT smell_type, COUNT(*) as count FROM code_smells GROUP BY smell_type ORDER BY count DESC"
    ).fetchall()

    # Refactoring types
    refactor_types = conn.execute(
        "SELECT refactor_type, COUNT(*) as count FROM refactoring_history GROUP BY refactor_type ORDER BY count DESC"
    ).fetchall()

    # Top projects by quality
    top_quality = conn.execute(
        """SELECT p.project_name, p.quality_score, u.name as owner
           FROM projects p JOIN users u ON p.user_id = u.id
           WHERE p.quality_score > 0
           ORDER BY p.quality_score DESC LIMIT 10"""
    ).fetchall()

    # Bottom projects by quality
    worst_quality = conn.execute(
        """SELECT p.project_name, p.quality_score, u.name as owner
           FROM projects p JOIN users u ON p.user_id = u.id
           WHERE p.quality_score > 0
           ORDER BY p.quality_score ASC LIMIT 10"""
    ).fetchall()

    # Most active users (by project count)
    active_users = conn.execute(
        """SELECT u.name, u.email, u.role, COUNT(p.id) as projects
           FROM users u LEFT JOIN projects p ON u.id = p.user_id
           GROUP BY u.id ORDER BY projects DESC LIMIT 10"""
    ).fetchall()

    # Dependency types
    dep_types = conn.execute(
        "SELECT type, COUNT(*) as count FROM dependencies GROUP BY type ORDER BY count DESC"
    ).fetchall()

    # AI suggestion acceptance rate
    total_ai = conn.execute("SELECT COUNT(*) as c FROM ai_suggestions").fetchone()["c"]
    accepted_ai = conn.execute("SELECT COUNT(*) as c FROM ai_suggestions WHERE accepted = 1").fetchone()["c"]

    conn.close()

    return {
        "smell_types": [dict(s) for s in smell_types],
        "refactor_types": [dict(r) for r in refactor_types],
        "top_quality_projects": [dict(p) for p in top_quality],
        "worst_quality_projects": [dict(p) for p in worst_quality],
        "most_active_users": [dict(u) for u in active_users],
        "dependency_types": [dict(d) for d in dep_types],
        "ai_acceptance": {
            "total": total_ai,
            "accepted": accepted_ai,
            "rate": round(accepted_ai / total_ai * 100, 1) if total_ai > 0 else 0
        }
    }


# ─── Activity Log ────────────────────────────────────────

@router.get("/activity")
def get_activity_log(current_user: dict = Depends(require_admin)):
    """Get admin activity log."""
    conn = get_connection()
    logs = conn.execute(
        """SELECT a.*, u.name as admin_name
           FROM admin_activity_log a JOIN users u ON a.admin_id = u.id
           ORDER BY a.created_at DESC LIMIT 100"""
    ).fetchall()
    conn.close()
    return [dict(l) for l in logs]
