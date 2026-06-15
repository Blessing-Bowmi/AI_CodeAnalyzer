"""
Database module - SQLite connection and schema creation.
Tables: users, projects, files, dependencies, code_smells, refactoring_history, ai_suggestions
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "codeanalyzer.db")


def get_connection():
    """Get a new SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database with all tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'developer',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name VARCHAR(200) NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            quality_score REAL DEFAULT 0,
            total_files INTEGER DEFAULT 0,
            total_functions INTEGER DEFAULT 0,
            total_classes INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path TEXT NOT NULL,
            content TEXT,
            language VARCHAR(50),
            loc INTEGER DEFAULT 0,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS parsed_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            name VARCHAR(255) NOT NULL,
            start_line INTEGER,
            end_line INTEGER,
            params TEXT,
            details TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            source VARCHAR(255) NOT NULL,
            target VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS code_smells (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            smell_type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            line INTEGER,
            description TEXT,
            suggestion TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS refactoring_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            refactor_type VARCHAR(100) NOT NULL,
            description TEXT,
            file_name VARCHAR(255),
            before_code TEXT,
            after_code TEXT,
            status VARCHAR(20) DEFAULT 'suggested',
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ai_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            suggestion TEXT NOT NULL,
            confidence_score REAL DEFAULT 0.0,
            category VARCHAR(50),
            risk_level VARCHAR(20) DEFAULT 'low',
            accepted INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS learning_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refactor_type VARCHAR(100) NOT NULL,
            was_accepted INTEGER NOT NULL,
            context TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admin_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(50),
            target_id INTEGER,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS review_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            data_json TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
    """)

    conn.commit()

    # ─── Seed permanent Admin account ─────────────────────
    existing = conn.execute("SELECT id FROM users WHERE email = ?", ("admin@codeanalyzer.com",)).fetchone()
    if not existing:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash("admin123")
        conn.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@codeanalyzer.com", hashed, "admin")
        )
        conn.commit()
        print("Default admin account created: admin@codeanalyzer.com / admin123")

    conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    init_db()
