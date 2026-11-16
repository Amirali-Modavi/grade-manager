from sqlite3 import IntegrityError
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from backend.database import (
    create_student_record,
    delete_student_record,
    get_all_students,
    update_student_record,
)
from backend.models import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentResponse])
def get_students():
    return get_all_students()


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student_data: StudentCreate):
    new_id = str(uuid4())
    try:
        return create_student_record(new_id, student_data.name, student_data.grades)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A student with this name already exists.")


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, student_data: StudentUpdate):
    try:
        updated = update_student_record(student_id, student_data.name, student_data.grades)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Another student already has this name.")
    if updated is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return updated


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: str):
    if not delete_student_record(student_id):
        raise HTTPException(status_code=404, detail="Student not found.")
    return None
