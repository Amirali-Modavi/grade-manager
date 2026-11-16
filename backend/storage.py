from pathlib import Path
import json

DATA_FILE = Path(__file__).resolve().parent / "students.json"


def load_students() -> list[dict]:
    if not DATA_FILE.exists():
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("The students.json file must contain a JSON list.")
    return data


def save_students(students: list[dict]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(students, file, ensure_ascii=False, indent=4)
