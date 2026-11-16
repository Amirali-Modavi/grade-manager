from fastapi import APIRouter

from backend.calculations import build_student_report
from backend.database import get_all_students

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/students")
def get_student_reports():
    return [build_student_report(student) for student in get_all_students()]


@router.get("/summary")
def get_class_summary():
    reports = [build_student_report(student) for student in get_all_students()]
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
    }
