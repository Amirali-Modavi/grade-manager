"""
Safely restore Grade Manager Stage 5 records from students_backup.json.
Run this script from the project root (the folder containing backend/).
It does not delete or overwrite existing student records.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKUP_JSON = ROOT / "students_backup.json"
BACKEND_DIR = ROOT / "backend"
DB_FILE = BACKEND_DIR / "grade_manager.db"


def main() -> None:
    if not BACKUP_JSON.exists():
        raise SystemExit(
            "students_backup.json was not found. Put it beside this script in the project root."
        )
    if not BACKEND_DIR.is_dir():
        raise SystemExit("backend folder was not found. Run this script from the Grade Manager project root.")

    records = json.loads(BACKUP_JSON.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("The backup must contain a JSON list.")

    BACKEND_DIR.mkdir(exist_ok=True)
    if DB_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        db_copy = DB_FILE.with_name(f"grade_manager.before_restore-{stamp}.db")
        shutil.copy2(DB_FILE, db_copy)
        print(f"Existing database backed up to: {db_copy.name}")

    imported = 0
    skipped = 0

    connection = sqlite3.connect(DB_FILE)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                grade REAL NOT NULL CHECK (grade >= 0 AND grade <= 20),
                position INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, position)
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        with connection:
            for record in records:
                student_id = str(record["id"])
                name = str(record["name"]).strip()
                grades = record.get("grades", [])

                if not name or not isinstance(grades, list):
                    raise ValueError(f"Invalid student record: {record!r}")
                if any(not isinstance(g, (int, float)) or not 0 <= float(g) <= 20 for g in grades):
                    raise ValueError(f"Invalid grade in record for {name!r}")

                existing_by_id = connection.execute(
                    "SELECT id FROM students WHERE id = ?", (student_id,)
                ).fetchone()
                existing_by_name = connection.execute(
                    "SELECT id FROM students WHERE name = ? COLLATE NOCASE", (name,)
                ).fetchone()

                if existing_by_id or existing_by_name:
                    skipped += 1
                    print(f"Skipped existing student: {name}")
                    continue

                connection.execute(
                    "INSERT INTO students (id, name) VALUES (?, ?)", (student_id, name)
                )
                connection.executemany(
                    "INSERT INTO grades (student_id, grade, position) VALUES (?, ?, ?)",
                    [(student_id, float(grade), index) for index, grade in enumerate(grades)],
                )
                imported += 1

            connection.execute(
                """INSERT INTO app_metadata (key, value)
                   VALUES ('json_migration_done', 'true')
                   ON CONFLICT(key) DO UPDATE SET value = 'true'"""
            )
    finally:
        connection.close()

    print()
    print(f"Restore complete. Imported: {imported}; skipped (already present): {skipped}.")
    print("Now restart the app with: uvicorn backend.main:app --reload")
    print("Then check: http://127.0.0.1:8000/api/reports/students")


if __name__ == "__main__":
    main()
