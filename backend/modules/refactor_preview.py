"""
Refactor Preview Engine (Innovative - Viva).
Shows Before vs After code with visual diff.
"""

import difflib
from database import get_connection


def get_preview(refactor_id: int) -> dict:
    """Generate before/after preview with diff for a refactoring."""
    conn = get_connection()
    refactor = conn.execute("SELECT * FROM refactoring_history WHERE id = ?", (refactor_id,)).fetchone()
    conn.close()
    
    if not refactor:
        return {"error": "Refactoring not found"}
    
    refactor_dict = dict(refactor)
    before = refactor_dict.get("before_code", "")
    after = refactor_dict.get("after_code", "")
    
    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile="before",
        tofile="after",
        lineterm=""
    ))
    
    # Generate HTML diff
    html_diff = difflib.HtmlDiff().make_table(
        before.splitlines(),
        after.splitlines(),
        fromdesc="Before Refactoring",
        todesc="After Refactoring"
    )
    
    # Line-by-line comparison
    changes = []
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in before_lines[i1:i2]:
                changes.append({"type": "unchanged", "content": line})
        elif tag == "delete":
            for line in before_lines[i1:i2]:
                changes.append({"type": "removed", "content": line})
        elif tag == "insert":
            for line in after_lines[j1:j2]:
                changes.append({"type": "added", "content": line})
        elif tag == "replace":
            for line in before_lines[i1:i2]:
                changes.append({"type": "removed", "content": line})
            for line in after_lines[j1:j2]:
                changes.append({"type": "added", "content": line})
    
    return {
        "refactor_id": refactor_id,
        "refactor_type": refactor_dict.get("refactor_type", ""),
        "file_name": refactor_dict.get("file_name", ""),
        "description": refactor_dict.get("description", ""),
        "before": before,
        "after": after,
        "diff": diff_lines,
        "changes": changes,
        "stats": {
            "lines_added": len([c for c in changes if c["type"] == "added"]),
            "lines_removed": len([c for c in changes if c["type"] == "removed"]),
            "lines_unchanged": len([c for c in changes if c["type"] == "unchanged"]),
        }
    }


def get_all_previews(project_id: int) -> list:
    """Get previews for all suggested refactorings in a project."""
    conn = get_connection()
    refactors = conn.execute(
        "SELECT id FROM refactoring_history WHERE project_id = ? AND status = 'suggested'",
        (project_id,)
    ).fetchall()
    conn.close()
    
    previews = []
    for r in refactors:
        preview = get_preview(r["id"])
        if "error" not in preview:
            previews.append(preview)
    return previews
