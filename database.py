import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(__file__), "resume_db.sqlite")
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = os.environ.get("USE_POSTGRES", "false").lower() == "true" or DATABASE_URL is not None


def get_connection():
    """Get database connection based on environment configuration."""
    if USE_POSTGRES:
        try:
            import psycopg2
            if DATABASE_URL:
                return psycopg2.connect(DATABASE_URL)
            return psycopg2.connect(
                host=os.environ.get("PG_HOST", "localhost"),
                database=os.environ.get("PG_DATABASE", "resume_db"),
                user=os.environ.get("PG_USER", "postgres"),
                password=os.environ.get("PG_PASSWORD", "password"),
                port=int(os.environ.get("PG_PORT", 5432))
            )
        except Exception as e:
            print(f"[Warning] Failed to connect to PostgreSQL ({e}). Falling back to SQLite.")

    # SQLite default
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize candidates table and ensure all columns exist."""
    conn = get_connection()
    cursor = conn.cursor()

    is_pg = hasattr(conn, "closed") and USE_POSTGRES

    if is_pg:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            github TEXT,
            education TEXT,
            skills TEXT,
            experience TEXT,
            ats_score REAL,
            filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            linkedin TEXT,
            github TEXT,
            education TEXT,
            skills TEXT,
            experience TEXT,
            ats_score REAL,
            filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    conn.commit()
    conn.close()


def insert_candidate(
    name: str,
    email: str,
    phone: str,
    education: str,
    skills: str,
    linkedin: str = "",
    github: str = "",
    experience: str = "",
    ats_score: Optional[float] = None,
    filename: str = ""
) -> int:
    """Insert a parsed candidate record into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    is_pg = hasattr(conn, "closed") and USE_POSTGRES

    if is_pg:
        query = """
        INSERT INTO candidates (name, email, phone, linkedin, github, education, skills, experience, ats_score, filename)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        cursor.execute(query, (name, email, phone, linkedin, github, education, skills, experience, ats_score, filename))
        new_id = cursor.fetchone()[0]
    else:
        query = """
        INSERT INTO candidates (name, email, phone, linkedin, github, education, skills, experience, ats_score, filename)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (name, email, phone, linkedin, github, education, skills, experience, ats_score, filename))
        new_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return new_id


def get_all_candidates(search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all candidates, optionally filtered by search keyword."""
    conn = get_connection()
    cursor = conn.cursor()
    is_pg = hasattr(conn, "closed") and USE_POSTGRES

    if search:
        term = f"%{search}%"
        if is_pg:
            query = """
            SELECT * FROM candidates 
            WHERE name ILIKE %s OR skills ILIKE %s OR education ILIKE %s OR email ILIKE %s
            ORDER BY id DESC
            """
            cursor.execute(query, (term, term, term, term))
        else:
            query = """
            SELECT * FROM candidates 
            WHERE name LIKE ? OR skills LIKE ? OR education LIKE ? OR email LIKE ?
            ORDER BY id DESC
            """
            cursor.execute(query, (term, term, term, term))
    else:
        cursor.execute("SELECT * FROM candidates ORDER BY id DESC")

    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_candidate_by_id(candidate_id: int) -> Optional[Dict[str, Any]]:
    """Get single candidate by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    is_pg = hasattr(conn, "closed") and USE_POSTGRES

    if is_pg:
        cursor.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
    else:
        cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_candidate(candidate_id: int) -> bool:
    """Delete candidate by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    is_pg = hasattr(conn, "closed") and USE_POSTGRES

    if is_pg:
        cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
    else:
        cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))

    conn.commit()
    conn.close()
    return True


# Auto-initialize database tables on module import
init_db()