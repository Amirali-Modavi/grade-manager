
import json
import sqlite3

import pytest

import backend.database as database


@pytest.fixture
def setup_database(monkeypatch, tmp_path):
    """Create an isolated temporary database for each test."""

    database_file = tmp_path / "test_grade_manager.db"
    legacy_file = tmp_path / "students.json"

    monkeypatch.setattr(database, "DATABASE_FILE", database_file)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", legacy_file)

    database.initialize_database()

    return database_file


def test_initialize_database_creates_tables(setup_database):
    with database.get_connection() as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

    table_names = {row["name"] for row in tables}

    assert "students" in table_names
    assert "grades" in table_names
    assert "app_metadata" in table_names


def test_get_all_students_returns_empty_list(setup_database):
    assert database.get_all_students() == []


def test_create_student_record(setup_database):
    result = database.create_student_record(
        "student-1",
        "Ali",
        [18.0, 19.0, 20.0]
    )

    assert result == {
        "id": "student-1",
        "name": "Ali",
        "grades": [18.0, 19.0, 20.0]
    }

    assert database.get_all_students() == [result]


def test_update_student_record(setup_database):
    database.create_student_record(
        "student-1",
        "Ali",
        [15.0, 16.0]
    )

    result = database.update_student_record(
        "student-1",
        "Ali Updated",
        [18.0, 19.0]
    )

    assert result == {
        "id": "student-1",
        "name": "Ali Updated",
        "grades": [18.0, 19.0]
    }

    assert database.get_all_students() == [result]


def test_update_nonexistent_student(setup_database):
    result = database.update_student_record(
        "unknown",
        "Nobody",
        [18.0]
    )

    assert result is None


def test_delete_student_record(setup_database):
    database.create_student_record(
        "student-1",
        "Ali",
        [18.0, 19.0]
    )

    result = database.delete_student_record("student-1")

    assert result is True
    assert database.get_all_students() == []


def test_delete_nonexistent_student(setup_database):
    assert database.delete_student_record("unknown") is False


def test_delete_student_cascades_to_grades(setup_database):
    database.create_student_record(
        "student-1",
        "Ali",
        [18.0, 19.0]
    )

    database.delete_student_record("student-1")

    with database.get_connection() as connection:
        grades = connection.execute(
            "SELECT * FROM grades WHERE student_id = ?",
            ("student-1",)
        ).fetchall()

    assert grades == []


def test_database_rolls_back_on_exception(setup_database):
    with pytest.raises(RuntimeError):
        with database.get_connection() as connection:
            connection.execute(
                "INSERT INTO students (id, name) VALUES (?, ?)",
                ("student-1", "Ali")
            )

            raise RuntimeError("Test rollback")

    assert database.get_all_students() == []


def test_database_rejects_invalid_grade_and_rolls_back(setup_database):
    with pytest.raises(sqlite3.IntegrityError):
        database.create_student_record(
            "student-1",
            "Ali",
            [18.0, 25.0]
        )

    assert database.get_all_students() == []


def test_database_rejects_duplicate_student_names(setup_database):
    database.create_student_record(
        "student-1",
        "Ali",
        [18.0]
    )

    with pytest.raises(sqlite3.IntegrityError):
        database.create_student_record(
            "student-2",
            "ali",
            [19.0]
        )

    assert len(database.get_all_students()) == 1


def test_database_migrates_legacy_json(monkeypatch, tmp_path):
    database_file = tmp_path / "migration.db"
    legacy_file = tmp_path / "students.json"

    legacy_students = [
        {
            "id": "old-1",
            "name": "Ali",
            "grades": [18, 19, 20]
        },
        {
            "id": "old-2",
            "name": "Sara",
            "grades": [17, 18]
        }
    ]

    legacy_file.write_text(
        json.dumps(legacy_students),
        encoding="utf-8"
    )

    monkeypatch.setattr(database, "DATABASE_FILE", database_file)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", legacy_file)

    database.initialize_database()

    students = database.get_all_students()

    assert students == [
        {
            "id": "old-1",
            "name": "Ali",
            "grades": [18.0, 19.0, 20.0]
        },
        {
            "id": "old-2",
            "name": "Sara",
            "grades": [17.0, 18.0]
        }
    ]


def test_database_migration_runs_only_once(monkeypatch, tmp_path):
    database_file = tmp_path / "migration.db"
    legacy_file = tmp_path / "students.json"

    legacy_file.write_text(
        json.dumps([
            {"id": "old-1", "name": "Ali", "grades": [18]}
        ]),
        encoding="utf-8"
    )

    monkeypatch.setattr(database, "DATABASE_FILE", database_file)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", legacy_file)

    database.initialize_database()

    legacy_file.write_text(
        json.dumps([
            {"id": "old-2", "name": "Sara", "grades": [19]}
        ]),
        encoding="utf-8"
    )

    database.initialize_database()

    students = database.get_all_students()

    assert len(students) == 1
    assert students[0]["id"] == "old-1"


def test_database_migration_skips_students_without_name_or_grades(
    monkeypatch, tmp_path
):
    database_file = tmp_path / "migration.db"
    legacy_file = tmp_path / "students.json"

    legacy_file.write_text(
        json.dumps([
            {"id": "1", "name": "", "grades": [18]},
            {"id": "2", "name": "Sara", "grades": []},
            {"id": "3", "name": "Ali", "grades": [19]}
        ]),
        encoding="utf-8"
    )

    monkeypatch.setattr(database, "DATABASE_FILE", database_file)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", legacy_file)

    database.initialize_database()

    students = database.get_all_students()

    assert len(students) == 1
    assert students[0]["id"] == "3"


def test_database_migration_rejects_invalid_json(
    monkeypatch, tmp_path
):
    database_file = tmp_path / "migration.db"
    legacy_file = tmp_path / "students.json"

    legacy_file.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(database, "DATABASE_FILE", database_file)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", legacy_file)

    with pytest.raises(RuntimeError, match="Could not read"):
        database.initialize_database()


def test_database_migration_rejects_non_list_json(
    monkeypatch, tmp_path
):
    database_file = tmp_path / "migration.db"
    legacy_file = tmp_path / "students.json"

    legacy_file.write_text(
        json.dumps({"name": "Ali"}),
        encoding="utf-8"
    )

    monkeypatch.setattr(database, "DATABASE_FILE", database_file)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", legacy_file)

    with pytest.raises(RuntimeError, match="JSON list"):
        database.initialize_database()
