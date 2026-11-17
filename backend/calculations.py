"""Grade calculations shared by reports and the performance chart."""
from decimal import Decimal, ROUND_HALF_UP

PASSING_THRESHOLD = 12.0
AVERAGE_DECIMAL_PLACES = 2


def calculate_average(grades: list[float]) -> float:
    if not grades:
        raise ValueError("Cannot calculate an average without grades.")
    return sum(grades) / len(grades)


def round_average(average: float) -> float:
    """Round for display and classification using conventional half-up rounding."""
    quantum = Decimal("1").scaleb(-AVERAGE_DECIMAL_PLACES)
    return float(Decimal(str(average)).quantize(quantum, rounding=ROUND_HALF_UP))


def calculate_letter_grade(average: float) -> str:
    if average >= 19.4:
        return "A+"
    elif average >= 18.6:
        return "A"
    elif average >= 18:
        return "A-"
    elif average >= 17.4:
        return "B+"
    elif average >= 16.6:
        return "B"
    elif average >= 16:
        return "B-"
    elif average >= 15.4:
        return "C+"
    elif average >= 14.6:
        return "C"
    elif average >= 14:
        return "C-"
    elif average >= 13.4:
        return "D+"
    elif average >= 12.6:
        return "D"
    elif average >= PASSING_THRESHOLD:
        return "D-"
    return "F"


def calculate_grade_status(letter_grade: str) -> str:
    if letter_grade.startswith("A"):
        return "Excellent"
    elif letter_grade.startswith("B"):
        return "Good"
    elif letter_grade.startswith("C"):
        return "Average"
    elif letter_grade.startswith("D"):
        return "Passing"
    return "Failing"


def build_student_report(student: dict) -> dict:
    average = round_average(calculate_average(student["grades"]))
    letter_grade = calculate_letter_grade(average)
    return {
        **student,
        "average": average,
        "letter_grade": letter_grade,
        "status": calculate_grade_status(letter_grade),
    }
