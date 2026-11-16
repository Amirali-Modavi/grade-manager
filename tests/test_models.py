
import pytest
from pydantic import ValidationError

from backend.models import StudentCreate, StudentUpdate


def test_create_student_with_valid_data():
    student = StudentCreate(
        name="Amirali",
        grades=[18, 19, 20]
    )

    assert student.name == "Amirali"
    assert student.grades == [18, 19, 20]


def test_student_name_is_stripped():
    student = StudentCreate(
        name="  Amirali  ",
        grades=[18, 19]
    )

    assert student.name == "Amirali"


@pytest.mark.parametrize("name", ["", "   "])
def test_invalid_student_name(name):
    with pytest.raises(ValidationError):
        StudentCreate(name=name, grades=[18, 19])


def test_student_name_max_length():
    with pytest.raises(ValidationError):
        StudentCreate(name="A" * 101, grades=[18, 19])


def test_empty_grades_are_rejected():
    with pytest.raises(ValidationError):
        StudentCreate(name="Amirali", grades=[])


@pytest.mark.parametrize("grade", [-1, 20.1, 25])
def test_invalid_grades_are_rejected(grade):
    with pytest.raises(ValidationError):
        StudentCreate(name="Amirali", grades=[18, grade])


def test_valid_boundary_grades():
    student = StudentCreate(
        name="Amirali",
        grades=[0, 20]
    )

    assert student.grades == [0, 20]


def test_student_update_with_valid_data():
    student = StudentUpdate(
        name="Ali",
        grades=[15, 18]
    )

    assert student.name == "Ali"
    assert student.grades == [15, 18]
