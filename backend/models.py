from pydantic import BaseModel, Field, field_validator


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    grades: list[float] = Field(min_length=1)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Student name cannot be empty.")
        return value

    @field_validator("grades")
    @classmethod
    def validate_grades(cls, values: list[float]) -> list[float]:
        if any(not 0 <= grade <= 20 for grade in values):
            raise ValueError("Every grade must be between 0 and 20.")
        return values


class StudentUpdate(StudentCreate):
    """The complete editable student record: name and grades."""


class StudentResponse(BaseModel):
    id: str
    name: str
    grades: list[float]
