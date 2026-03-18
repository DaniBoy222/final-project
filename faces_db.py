"""
faces_db.py

SQLite helper for storing information about known faces.
This does NOT store the raw face images (you already keep those
as files in the "known_faces" folder). It stores:

- which person (name)
- which image file path
- optional email or notes
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path("faces.db")


def init_db(db_path: Path = DB_PATH) -> None:
    """
    Create the database file and faces table if they don't exist.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image_path TEXT NOT NULL UNIQUE,
            email TEXT,
            notes TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def add_or_update_face(
    name: str,
    image_path: str,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> None:
    """
    Add a new face entry or update it if the image_path already exists.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO faces (name, image_path, email, notes)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(image_path) DO UPDATE SET
            name = excluded.name,
            email = excluded.email,
            notes = excluded.notes
        """,
        (name, image_path, email, notes),
    )
    conn.commit()
    conn.close()


def get_all_faces(db_path: Path = DB_PATH) -> List[Dict]:
    """
    Return all face records as a list of dicts.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM faces ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_face_by_name(name: str, db_path: Path = DB_PATH) -> List[Dict]:
    """
    Return all faces with the given name (you may have multiple images).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM faces WHERE name = ?", (name,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_primary_email_for_name(name: str, db_path: Path = DB_PATH) -> Optional[str]:
    """
    Return the first non-null email for this person, if any.
    Useful if you want different alert behavior per person later.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT email FROM faces WHERE name = ? AND email IS NOT NULL LIMIT 1",
        (name,),
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


if __name__ == "__main__":
    """
    Simple CLI example:
    - Initializes the DB
    - Prints all current faces
    """
    init_db()
    print("Database initialized at:", DB_PATH.resolve())
    faces = get_all_faces()
    if not faces:
        print("No faces stored yet. Example of how to add one:")
        print(
            '  from faces_db import add_or_update_face; '
            "add_or_update_face('Alice', 'known_faces/Alice.jpg', 'alice@example.com')"
        )
    else:
        print("Stored faces:")
        for f in faces:
            print(f" - {f['name']} ({f['image_path']}) email={f.get('email')}")

