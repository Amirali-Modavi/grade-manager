from fastapi import APIRouter

from backend.calculations import PASSING_THRESHOLD, build_student_report
from backend.database import get_all_students

router = APIRouter(prefix="/reports", tags=["Reports"])


def _build_reports() -> list[dict]:
    return [build_student_report(student) for student in get_all_students() if student["grades"]]


def _build_class_summary(reports: list[dict]) -> dict:
    count = len(reports)
    average = sum(item["average"] for item in reports) / count if count else 0
    return {
        "total_students": count,
        "class_average": round(average, 2),
        "excellent_count": sum(item["status"] == "Excellent" for item in reports),
        "good_count": sum(item["status"] == "Good" for item in reports),
        "average_count": sum(item["status"] == "Average" for item in reports),
        "passing_count": sum(item["status"] == "Passing" for item in reports),
        "failing_count": sum(item["status"] == "Failing" for item in reports),
        "passing_threshold": PASSING_THRESHOLD,
    }


@router.get("/overview")
def get_reports_overview():
    """Return report rows and dashboard summary from one database read."""
    reports = _build_reports()
    return {"students": reports, "summary": _build_class_summary(reports)}


@router.get("/students")
def get_student_reports():
    return _build_reports()


@router.get("/summary")
def get_class_summary():
    return _build_class_summary(_build_reports())
