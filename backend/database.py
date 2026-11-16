"""SQLite database setup and one-time import from the Stage 4 JSON file."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BACKEND_DIR / "grade_manager.db"
LEGACY_JSON_FILE = BACKEND_DIR / "students.json"


@contextmanager
def get_connection():
    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create tables and import existing JSON records once, preserving IDs."""
    with get_connection() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                grade REAL NOT NULL CHECK (grade >= 0 AND grade <= 20),
                position INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, position)
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )"""
        )

        migrated = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'json_migration_done'"
        ).fetchone()
        if migrated is None:
            if LEGACY_JSON_FILE.exists():
                try:
                    legacy_students = json.loads(LEGACY_JSON_FILE.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError) as exc:
                    raise RuntimeError(
                        "Could not read backend/students.json. Fix or restore this file before starting Stage 5."
                    ) from exc
                if not isinstance(legacy_students, list):
                    raise RuntimeError("backend/students.json must contain a JSON list.")
                for student in legacy_students:
                    student_id = str(student["id"])
                    name = str(student["name"]).strip()
                    grades = student.get("grades", [])
                    if not name or not grades:
                        continue
                    connection.execute(
                        "INSERT OR IGNORE INTO students (id, name) VALUES (?, ?)",
                        (student_id, name),
                    )
                    for position, grade in enumerate(grades):
                        connection.execute(
                            "INSERT OR IGNORE INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
                            (student_id, float(grade), position),
                        )
            connection.execute(
                "INSERT INTO app_metadata (key, value) VALUES ('json_migration_done', 'true')"
            )


def get_all_students() -> list[dict]:
    with get_connection() as connection:
        student_rows = connection.execute(
            "SELECT id, name FROM students ORDER BY rowid"
        ).fetchall()
        result = []
        for student in student_rows:
            grade_rows = connection.execute(
                "SELECT grade FROM grades WHERE student_id = ? ORDER BY position",
                (student["id"],),
            ).fetchall()
            result.append({
                "id": student["id"],
                "name": student["name"],
                "grades": [row["grade"] for row in grade_rows],
            })
        return result


def create_student_record(student_id: str, name: str, grades: list[float]) -> dict:
    with get_connection() as connection:
        connection.execute("INSERT INTO students (id, name) VALUES (?, ?)", (student_id, name))
        connection.executemany(
            "INSERT INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
            [(student_id, grade, index) for index, grade in enumerate(grades)],
        )
    return {"id": student_id, "name": name, "grades": grades}


def update_student_record(student_id: str, name: str, grades: list[float]) -> dict | None:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE students SET name = ? WHERE id = ?", (name, student_id)
        )
        if cursor.rowcount == 0:
            return None
        connection.execute("DELETE FROM grades WHERE student_id = ?", (student_id,))
        connection.executemany(
            "INSERT INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
            [(student_id, grade, index) for index, grade in enumerate(grades)],
        )
    return {"id": student_id, "name": name, "grades": grades}


def delete_student_record(student_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
        return cursor.rowcount > 0
