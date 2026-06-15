"""
Code Upload Module - Accept ZIP files, extract, store metadata.
"""

import os
import zipfile
import shutil
import tempfile
from datetime import datetime
from database import get_connection


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
EXTRACT_DIR = os.path.join(os.path.dirname(__file__), "..", "extracted")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.cs', '.rb', '.go', '.php'}


def handle_upload(file_bytes: bytes, filename: str, user_id: int) -> dict:
    """Process uploaded ZIP file."""
    project_name = os.path.splitext(filename)[0]
    
    # Save ZIP
    zip_path = os.path.join(UPLOAD_DIR, filename)
    with open(zip_path, 'wb') as f:
        f.write(file_bytes)
    
    # Extract
    extract_path = os.path.join(EXTRACT_DIR, f"{project_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    os.makedirs(extract_path, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file")
    
    # Store in database
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO projects (user_id, project_name, upload_date) VALUES (?, ?, ?)",
        (user_id, project_name, datetime.now().isoformat())
    )
    project_id = cursor.lastrowid
    
    # Walk extracted files and store metadata
    file_count = 0
    for root, dirs, files in os.walk(extract_path):
        # Skip hidden directories and common non-code directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__', 'venv', '.git')]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, extract_path)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    loc = len(content.splitlines())
                except Exception:
                    content = ""
                    loc = 0
                
                lang = _detect_language(ext)
                conn.execute(
                    "INSERT INTO files (project_id, file_name, file_path, content, language, loc) VALUES (?, ?, ?, ?, ?, ?)",
                    (project_id, fname, rel_path, content, lang, loc)
                )
                file_count += 1
    
    conn.execute("UPDATE projects SET total_files = ? WHERE id = ?", (file_count, project_id))
    conn.commit()
    conn.close()
    
    # Clean up ZIP
    try:
        os.remove(zip_path)
    except Exception:
        pass
    
    return {
        "project_id": project_id,
        "project_name": project_name,
        "files_extracted": file_count,
        "extract_path": extract_path
    }


def _detect_language(ext: str) -> str:
    lang_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.jsx': 'javascript', '.tsx': 'typescript', '.java': 'java',
        '.c': 'c', '.cpp': 'cpp', '.h': 'c', '.cs': 'csharp',
        '.rb': 'ruby', '.go': 'go', '.php': 'php'
    }
    return lang_map.get(ext, 'unknown')


def get_project_files(project_id: int) -> list:
    """Get all files for a project."""
    conn = get_connection()
    files = conn.execute("SELECT * FROM files WHERE project_id = ?", (project_id,)).fetchall()
    conn.close()
    return [dict(f) for f in files]
