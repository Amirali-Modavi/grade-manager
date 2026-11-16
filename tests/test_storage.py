
import json

import pytest

import backend.storage as storage


def test_load_students_when_file_does_not_exist(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "DATA_FILE", tmp_path / "students.json")

    assert storage.load_students() == []


def test_load_students_from_json_file(monkeypatch, tmp_path):
    data_file = tmp_path / "students.json"
    students = [
        {"id": "1", "name": "Ali", "grades": [18, 19, 20]}
    ]

    data_file.write_text(
        json.dumps(students),
        encoding="utf-8"
    )

    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    assert storage.load_students() == students


def test_load_students_rejects_non_list_json(monkeypatch, tmp_path):
    data_file = tmp_path / "students.json"
    data_file.write_text('{"name": "Ali"}', encoding="utf-8")

    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    with pytest.raises(ValueError, match="JSON list"):
        storage.load_students()


def test_save_students_creates_json_file(monkeypatch, tmp_path):
    data_file = tmp_path / "students.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    students = [
        {"id": "1", "name": "علی", "grades": [18, 19, 20]}
    ]

    storage.save_students(students)

    assert data_file.exists()

    saved_data = json.loads(data_file.read_text(encoding="utf-8"))

    assert saved_data == students
    assert "علی" in data_file.read_text(encoding="utf-8")


def test_save_and_load_students_round_trip(monkeypatch, tmp_path):
    data_file = tmp_path / "students.json"
    monkeypatch.setattr(storage, "DATA_FILE", data_file)

    students = [
        {"id": "1", "name": "Ali", "grades": [17.5, 19, 20]},
        {"id": "2", "name": "Sara", "grades": [18, 19.5]}
    ]

    storage.save_students(students)

    assert storage.load_students() == students
