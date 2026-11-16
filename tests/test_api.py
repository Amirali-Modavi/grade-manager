
import pytest
from fastapi.testclient import TestClient

import backend.database as database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Use a separate temporary database for every test.
    test_database = tmp_path / "test_grade_manager.db"

    monkeypatch.setattr(database, "DATABASE_FILE", test_database)
    monkeypatch.setattr(
        database,
        "LEGACY_JSON_FILE",
        tmp_path / "students.json"
    )

    with TestClient(app) as test_client:
        yield test_client


def test_get_students(client):
    response = client.get("/api/students")

    assert response.status_code == 200
    assert response.json() == []


def test_create_student(client):
    response = client.post(
        "/api/students",
        json={
            "name": "Amirali",
            "grades": [18, 19, 20]
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Amirali"
    assert response.json()["grades"] == [18, 19, 20]


def test_create_duplicate_student(client):
    student_data = {
        "name": "Amirali",
        "grades": [18, 19]
    }

    client.post("/api/students", json=student_data)

    duplicate_response = client.post(
        "/api/students",
        json={
            "name": "amirali",
            "grades": [15, 16]
        }
    )

    assert duplicate_response.status_code == 409


def test_create_student_with_invalid_grade(client):
    response = client.post(
        "/api/students",
        json={
            "name": "Ali",
            "grades": [18, 25]
        }
    )

    assert response.status_code == 422


def test_update_student(client):
    create_response = client.post(
        "/api/students",
        json={
            "name": "Ali",
            "grades": [15, 16]
        }
    )

    student_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/students/{student_id}",
        json={
            "name": "Ali Updated",
            "grades": [18, 19, 20]
        }
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Ali Updated"
    assert update_response.json()["grades"] == [18, 19, 20]


def test_update_nonexistent_student(client):
    response = client.put(
        "/api/students/nonexistent-id",
        json={
            "name": "Ali",
            "grades": [18, 19]
        }
    )

    assert response.status_code == 404


def test_delete_student(client):
    create_response = client.post(
        "/api/students",
        json={
            "name": "Yousef",
            "grades": [17, 18]
        }
    )

    student_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/students/{student_id}"
    )

    assert delete_response.status_code == 204

    students_response = client.get("/api/students")
    assert students_response.json() == []


def test_delete_nonexistent_student(client):
    response = client.delete("/api/students/nonexistent-id")

    assert response.status_code == 404


def test_student_reports(client):
    client.post(
        "/api/students",
        json={
            "name": "Amirali",
            "grades": [18, 20]
        }
    )

    response = client.get("/api/reports/students")

    assert response.status_code == 200

    report = response.json()[0]

    assert report["average"] == 19
    assert report["letter_grade"] == "A"
    assert report["status"] == "Excellent"


def test_class_summary(client):
    client.post(
        "/api/students",
        json={
            "name": "Amirali",
            "grades": [18, 20]
        }
    )

    response = client.get("/api/reports/summary")

    assert response.status_code == 200
    assert response.json()["total_students"] == 1
    assert response.json()["class_average"] == 19
    assert response.json()["excellent_count"] == 1

def test_update_student_with_duplicate_name(client):
    first_response = client.post(
        "/api/students",
        json={
            "name": "Ali",
            "grades": [18, 19],
        },
    )

    second_response = client.post(
        "/api/students",
        json={
            "name": "Reza",
            "grades": [16, 17],
        },
    )

    second_student_id = second_response.json()["id"]

    update_response = client.put(
        f"/api/students/{second_student_id}",
        json={
            "name": "Ali",
            "grades": [19, 20],
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert update_response.status_code == 409

def test_update_student_with_duplicate_name(client):
    first_response = client.post(
        "/api/students",
        json={"name": "Ali", "grades": [18, 19]},
    )

    second_response = client.post(
        "/api/students",
        json={"name": "Reza", "grades": [16, 17]},
    )

    second_student_id = second_response.json()["id"]

    update_response = client.put(
        f"/api/students/{second_student_id}",
        json={"name": "Ali", "grades": [19, 20]},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert update_response.status_code == 409
def test_update_student_with_duplicate_name(client):
    client.post(
        "/api/students",
        json={"name": "Ali", "grades": [18, 19]},
    )

    second_response = client.post(
        "/api/students",
        json={"name": "Reza", "grades": [16, 17]},
    )

    second_student_id = second_response.json()["id"]

    response = client.put(
        f"/api/students/{second_student_id}",
        json={"name": "Ali", "grades": [19, 20]},
    )

    assert response.status_code == 409
def test_frontend_homepage(client):
    response = client.get("/")

    assert response.status_code == 200

def test_health_check(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "Grade Manager API is running with SQLite",
    }
