import pytest
from fastapi.testclient import TestClient

import backend.database as database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_database = tmp_path / "test_grade_manager.db"
    monkeypatch.setattr(database, "DATABASE_FILE", test_database)
    monkeypatch.setattr(database, "LEGACY_JSON_FILE", tmp_path / "students.json")
    with TestClient(app) as test_client:
        yield test_client


def test_get_students(client):
    response = client.get("/api/students")
    assert response.status_code == 200
    assert response.json() == []


def test_create_student(client):
    response = client.post("/api/students", json={"name": "Amirali", "grades": [18, 19, 20]})
    assert response.status_code == 201
    assert response.json()["name"] == "Amirali"
    assert response.json()["grades"] == [18, 19, 20]


def test_create_duplicate_student(client):
    client.post("/api/students", json={"name": "Amirali", "grades": [18, 19]})
    response = client.post("/api/students", json={"name": "amirali", "grades": [15, 16]})
    assert response.status_code == 409


@pytest.mark.parametrize(
    "first_name, duplicate_name",
    [("Élise", "élise"), ("علی", "علي"), ("کاظم", "كاظم")],
)
def test_create_student_rejects_unicode_equivalent_names(client, first_name, duplicate_name):
    first = client.post("/api/students", json={"name": first_name, "grades": [18]})
    second = client.post("/api/students", json={"name": duplicate_name, "grades": [19]})
    assert first.status_code == 201
    assert second.status_code == 409


def test_create_student_with_invalid_grade(client):
    response = client.post("/api/students", json={"name": "Ali", "grades": [18, 25]})
    assert response.status_code == 422


def test_update_student(client):
    created = client.post("/api/students", json={"name": "Ali", "grades": [15, 16]})
    student_id = created.json()["id"]
    response = client.put(f"/api/students/{student_id}", json={"name": "Ali Updated", "grades": [18, 19, 20]})
    assert response.status_code == 200
    assert response.json()["name"] == "Ali Updated"
    assert response.json()["grades"] == [18, 19, 20]


def test_update_student_with_duplicate_name(client):
    first = client.post("/api/students", json={"name": "Ali", "grades": [18, 19]})
    second = client.post("/api/students", json={"name": "Reza", "grades": [16, 17]})
    response = client.put(
        f"/api/students/{second.json()['id']}",
        json={"name": first.json()["name"], "grades": [19, 20]},
    )
    assert response.status_code == 409


def test_update_nonexistent_student(client):
    response = client.put("/api/students/nonexistent-id", json={"name": "Ali", "grades": [18, 19]})
    assert response.status_code == 404


def test_delete_student(client):
    created = client.post("/api/students", json={"name": "Yousef", "grades": [17, 18]})
    response = client.delete(f"/api/students/{created.json()['id']}")
    assert response.status_code == 204
    assert client.get("/api/students").json() == []


def test_delete_nonexistent_student(client):
    assert client.delete("/api/students/nonexistent-id").status_code == 404


def test_student_reports(client):
    client.post("/api/students", json={"name": "Amirali", "grades": [18, 20]})
    response = client.get("/api/reports/students")
    assert response.status_code == 200
    report = response.json()[0]
    assert report["average"] == 19
    assert report["letter_grade"] == "A"
    assert report["status"] == "Excellent"


def test_report_uses_the_displayed_rounded_average_for_classification(client):
    client.post("/api/students", json={"name": "Near pass", "grades": [11.996]})
    response = client.get("/api/reports/students")
    assert response.status_code == 200
    assert response.json()[0]["average"] == 12.0
    assert response.json()[0]["letter_grade"] == "D-"
    assert response.json()[0]["status"] == "Passing"


def test_class_summary(client):
    client.post("/api/students", json={"name": "Amirali", "grades": [18, 20]})
    response = client.get("/api/reports/summary")
    assert response.status_code == 200
    assert response.json()["total_students"] == 1
    assert response.json()["class_average"] == 19
    assert response.json()["excellent_count"] == 1
    assert response.json()["passing_threshold"] == 12.0


def test_overview_combines_students_summary_and_threshold(client):
    client.post("/api/students", json={"name": "Amirali", "grades": [18, 20]})
    response = client.get("/api/reports/overview")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["students"]) == 1
    assert payload["summary"]["total_students"] == 1
    assert payload["summary"]["passing_threshold"] == 12.0


def test_reports_do_not_crash_on_legacy_student_without_grades(client):
    with database.get_connection() as connection:
        connection.execute("INSERT INTO students (id, name) VALUES (?, ?)", ("bad", "No grades"))
    # Startup cleanup removes invalid legacy rows rather than letting reporting raise ValueError.
    database.initialize_database()
    assert client.get("/api/reports/students").status_code == 200
    assert client.get("/api/reports/summary").status_code == 200


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
