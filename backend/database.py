"""SQLite persistence and validated one-time import from legacy JSON."""
from __future__ import annotations

import json
import logging
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from backend.names import normalize_student_name, student_name_key

logger = logging.getLogger(__name__)
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


def _create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            name_key TEXT
        )"""
    )
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(students)")}
    if "name_key" not in columns:
        connection.execute("ALTER TABLE students ADD COLUMN name_key TEXT")

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


def _backfill_name_keys(connection: sqlite3.Connection) -> None:
    """Backfill keys while retaining any pre-existing duplicate legacy rows."""
    seen_keys: set[str] = set()
    rows = connection.execute("SELECT id, name FROM students ORDER BY rowid").fetchall()
    for row in rows:
        # Preserve the existing display value during schema upgrades; only the
        # comparison key is normalized so the migration cannot violate the old
        # ASCII-only UNIQUE constraint while preserving legacy data.
        key = student_name_key(row["name"])
        if not key:
            # Keep the legacy row visible for inspection, but do not let an
            # empty key block all future inserts.
            stored_key = None
        elif key in seen_keys:
            # Existing databases may already contain Unicode-equivalent names.
            # Preserve both records, log the conflict, and enforce uniqueness
            # for every new or edited record through _ensure_name_available.
            stored_key = None
            logger.warning(
                "Existing duplicate student name found during normalization: %r (id=%s). "
                "The record was preserved; new duplicates will be rejected.",
                row["name"],
                row["id"],
            )
        else:
            seen_keys.add(key)
            stored_key = key
        connection.execute(
            "UPDATE students SET name = ?, name_key = ? WHERE id = ?",
            (row["name"], stored_key, row["id"]),
        )
    connection.execute(
        """CREATE UNIQUE INDEX IF NOT EXISTS idx_students_name_key_unique
           ON students(name_key) WHERE name_key IS NOT NULL"""
    )


def _validate_legacy_record(record: object) -> tuple[str, str, list[float]]:
    if not isinstance(record, dict):
        raise ValueError("record must be a JSON object")

    raw_id = record.get("id")
    raw_name = record.get("name")
    grades = record.get("grades")
    if raw_id is None or not str(raw_id).strip():
        raise ValueError("student id is missing or empty")
    if not isinstance(raw_name, str):
        raise ValueError("student name must be a string")
    name = normalize_student_name(raw_name)
    if not name:
        raise ValueError("student name is empty")
    if len(name) > 100:
        raise ValueError("student name exceeds 100 characters")
    if not isinstance(grades, list) or not grades:
        raise ValueError("grades must be a non-empty list")

    validated_grades: list[float] = []
    for grade_index, grade in enumerate(grades, start=1):
        if isinstance(grade, bool) or not isinstance(grade, (int, float)):
            raise ValueError(f"grade #{grade_index} must be a number")
        numeric_grade = float(grade)
        if not math.isfinite(numeric_grade) or not 0 <= numeric_grade <= 20:
            raise ValueError(f"grade #{grade_index} must be a finite number between 0 and 20")
        validated_grades.append(numeric_grade)

    return str(raw_id).strip(), name, validated_grades


def _ensure_name_available(
    connection: sqlite3.Connection,
    name: str,
    exclude_student_id: str | None = None,
) -> str:
    normalized_name = normalize_student_name(name)
    key = student_name_key(normalized_name)
    if not key:
        raise sqlite3.IntegrityError("Student name cannot be empty")

    rows = connection.execute("SELECT id, name FROM students").fetchall()
    for row in rows:
        if row["id"] != exclude_student_id and student_name_key(row["name"]) == key:
            raise sqlite3.IntegrityError("A student with this normalized name already exists")
    return key


def _migrate_legacy_json(connection: sqlite3.Connection) -> None:
    migrated = connection.execute(
        "SELECT value FROM app_metadata WHERE key = 'json_migration_done'"
    ).fetchone()
    if migrated is not None:
        return

    imported = 0
    rejected = 0
    if LEGACY_JSON_FILE.exists():
        try:
            legacy_students = json.loads(LEGACY_JSON_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(
                "Could not read backend/students.json. Fix or restore this file before starting the application."
            ) from exc
        if not isinstance(legacy_students, list):
            raise RuntimeError("backend/students.json must contain a JSON list.")

        for index, raw_record in enumerate(legacy_students, start=1):
            savepoint = f"legacy_student_{index}"
            connection.execute(f"SAVEPOINT {savepoint}")
            try:
                student_id, name, grades = _validate_legacy_record(raw_record)
                if connection.execute(
                    "SELECT 1 FROM students WHERE id = ?", (student_id,)
                ).fetchone():
                    raise ValueError(f"student id {student_id!r} already exists")

                name_key = _ensure_name_available(connection, name)
                connection.execute(
                    "INSERT INTO students (id, name, name_key) VALUES (?, ?, ?)",
                    (student_id, name, name_key),
                )
                connection.executemany(
                    "INSERT INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
                    [(student_id, grade, position) for position, grade in enumerate(grades)],
                )
            except (ValueError, sqlite3.IntegrityError, TypeError) as exc:
                connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                rejected += 1
                logger.warning(
                    "Rejected legacy student JSON record #%s: %s. The entire record was skipped.",
                    index,
                    exc,
                )
            else:
                connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                imported += 1

    connection.execute(
        "INSERT INTO app_metadata (key, value) VALUES ('json_migration_done', 'true')"
    )
    logger.info(
        "Legacy JSON migration finished: %s imported, %s rejected.", imported, rejected
    )


def _remove_invalid_existing_records(connection: sqlite3.Connection) -> None:
    """Remove rows left empty by older migrations that silently ignored grades."""
    invalid_rows = connection.execute(
        """SELECT s.id, s.name
           FROM students AS s
           WHERE TRIM(s.name) = '' OR NOT EXISTS (
               SELECT 1 FROM grades AS g WHERE g.student_id = s.id
           ) OR EXISTS (
               SELECT 1 FROM grades AS g
               WHERE g.student_id = s.id AND (g.grade < 0 OR g.grade > 20 OR g.grade IS NULL)
           )"""
    ).fetchall()
    for row in invalid_rows:
        logger.warning(
            "Removing invalid legacy student record %r (id=%s): it has no grades or contains an invalid grade.",
            row["name"],
            row["id"],
        )
        connection.execute("DELETE FROM students WHERE id = ?", (row["id"],))


def initialize_database() -> None:
    """Create or upgrade the schema, then safely import legacy JSON once."""
    with get_connection() as connection:
        _create_tables(connection)
        _backfill_name_keys(connection)
        _migrate_legacy_json(connection)
        _remove_invalid_existing_records(connection)


def get_all_students() -> list[dict]:
    """Load every student and grade in one query (avoids an N+1 query pattern)."""
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT s.id, s.name, g.grade
               FROM students AS s
               LEFT JOIN grades AS g ON g.student_id = s.id
               ORDER BY s.rowid, g.position"""
        ).fetchall()

    students: list[dict] = []
    for row in rows:
        if not students or students[-1]["id"] != row["id"]:
            students.append({"id": row["id"], "name": row["name"], "grades": []})
        if row["grade"] is not None:
            students[-1]["grades"].append(row["grade"])
    return students


def create_student_record(student_id: str, name: str, grades: list[float]) -> dict:
    normalized_name = normalize_student_name(name)
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        name_key = _ensure_name_available(connection, normalized_name)
        if not grades:
            raise sqlite3.IntegrityError("A student must have at least one grade")
        connection.execute(
            "INSERT INTO students (id, name, name_key) VALUES (?, ?, ?)",
            (student_id, normalized_name, name_key),
        )
        connection.executemany(
            "INSERT INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
            [(student_id, grade, index) for index, grade in enumerate(grades)],
        )
    return {"id": student_id, "name": normalized_name, "grades": grades}


def update_student_record(student_id: str, name: str, grades: list[float]) -> dict | None:
    normalized_name = normalize_student_name(name)
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if connection.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone() is None:
            return None
        name_key = _ensure_name_available(connection, normalized_name, exclude_student_id=student_id)
        if not grades:
            raise sqlite3.IntegrityError("A student must have at least one grade")
        connection.execute(
            "UPDATE students SET name = ?, name_key = ? WHERE id = ?",
            (normalized_name, name_key, student_id),
        )
        connection.execute("DELETE FROM grades WHERE student_id = ?", (student_id,))
        connection.executemany(
            "INSERT INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
            [(student_id, grade, index) for index, grade in enumerate(grades)],
        )
    return {"id": student_id, "name": normalized_name, "grades": grades}


def delete_student_record(student_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
        return cursor.rowcount > 0
