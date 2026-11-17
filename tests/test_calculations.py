import pytest

from backend.calculations import (
    PASSING_THRESHOLD,
    build_student_report,
    calculate_average,
    calculate_grade_status,
    calculate_letter_grade,
    round_average,
)


def test_calculate_average():
    assert calculate_average([18, 19, 20]) == 19


def test_calculate_average_with_empty_list():
    with pytest.raises(ValueError):
        calculate_average([])


def test_calculate_average_with_decimal_grades():
    assert calculate_average([18.5, 19.5, 20]) == pytest.approx(19.3333333333)


@pytest.mark.parametrize(
    "average, expected",
    [
        (20, "A+"), (19.4, "A+"), (19.39, "A"), (18.6, "A"),
        (18.59, "A-"), (18, "A-"), (17.99, "B+"), (17.4, "B+"),
        (17.39, "B"), (16.6, "B"), (16.59, "B-"), (16, "B-"),
        (15.99, "C+"), (15.4, "C+"), (15.39, "C"), (14.6, "C"),
        (14.59, "C-"), (14, "C-"), (13.99, "D+"), (13.4, "D+"),
        (13.39, "D"), (12.6, "D"), (12.59, "D-"), (12, "D-"),
        (11.99, "F"), (10, "F"), (0, "F"),
    ],
)
def test_calculate_letter_grade(average, expected):
    assert calculate_letter_grade(average) == expected


def test_pass_threshold_is_the_letter_grade_boundary():
    assert PASSING_THRESHOLD == 12.0
    assert calculate_letter_grade(PASSING_THRESHOLD) == "D-"
    assert calculate_letter_grade(PASSING_THRESHOLD - 0.01) == "F"


@pytest.mark.parametrize(
    "letter_grade, expected",
    [("A+", "Excellent"), ("B", "Good"), ("C", "Average"), ("D-", "Passing"), ("F", "Failing")],
)
def test_calculate_grade_status(letter_grade, expected):
    assert calculate_grade_status(letter_grade) == expected


def test_round_average_uses_half_up_rounding():
    assert round_average(11.996) == 12.0
    assert round_average(12.125) == 12.13


def test_build_student_report_uses_rounded_average_for_letter_grade():
    student = {"id": "student-1", "name": "Ali", "grades": [11.996]}

    result = build_student_report(student)

    assert result["average"] == 12.0
    assert result["letter_grade"] == "D-"
    assert result["status"] == "Passing"


def test_build_student_report():
    student = {"id": "student-1", "name": "Ali", "grades": [18.0, 19.0, 20.0]}
    result = build_student_report(student)
    assert result == {
        "id": "student-1", "name": "Ali", "grades": [18.0, 19.0, 20.0],
        "average": 19.0, "letter_grade": "A", "status": "Excellent",
    }


def test_build_student_report_does_not_modify_original_student():
    student = {"id": "student-1", "name": "Ali", "grades": [18.0, 19.0, 20.0]}
    original = student.copy()
    build_student_report(student)
    assert student == original


def test_build_student_report_rejects_empty_grades():
    with pytest.raises(ValueError):
        build_student_report({"id": "student-1", "name": "Ali", "grades": []})
