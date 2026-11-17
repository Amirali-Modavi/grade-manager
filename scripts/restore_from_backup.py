"""Restore additional student records from a local students_backup.json file.

Run from the project root with:
    python -m scripts.restore_from_backup

The script backs up the current SQLite database before importing and never
replaces existing student IDs or normalized names.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
import sqlite3

from backend.database import DATABASE_FILE, create_student_record, initialize_database
from backend.models import StudentCreate
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
BACKUP_JSON = ROOT / "students_backup.json"


def main() -> None:
    if not BACKUP_JSON.exists():
        raise SystemExit(
            "students_backup.json was not found. Put the backup beside the README file."
        )

    try:
        records = json.loads(BACKUP_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read students_backup.json: {exc}") from exc
    if not isinstance(records, list):
        raise SystemExit("The backup must contain a JSON list.")

    if DATABASE_FILE.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DATABASE_FILE.with_name(
            f"{DATABASE_FILE.stem}.before-restore-{stamp}.db"
        )
        shutil.copy2(DATABASE_FILE, backup_path)
        print(f"Existing database backed up to: {backup_path.name}")

    initialize_database()
    imported = 0
    skipped = 0
    for index, record in enumerate(records, start=1):
        try:
            if (
                not isinstance(record, dict)
                or record.get("id") is None
                or not str(record.get("id")).strip()
            ):
                raise ValueError("record must contain a non-empty id")
            student = StudentCreate.model_validate(
                {"name": record.get("name"), "grades": record.get("grades")}
            )
            create_student_record(str(record["id"]).strip(), student.name, student.grades)
            imported += 1
        except (ValueError, TypeError, sqlite3.IntegrityError, ValidationError) as exc:
            skipped += 1
            logging.warning("Skipped backup record #%s: %s", index, exc)

    print(f"Restore complete. Imported: {imported}; skipped: {skipped}.")


if __name__ == "__main__":
    main()
