import json
from dataclasses import dataclass

with open("info_two_classes.json", encoding="utf-8") as f:
    data = json.load(f)


DAYS: int = data["days"]
PERIODS: int = data["periods"]
TEACHERS: int = data["teachers"]
CLASSES: int = data["classes"]
ROOMS: int = data["rooms"]
SUBJECTS = len(data["subjects"])


@dataclass
class SubjectInfo:
    classes: list[int]
    teachers: list[int]
    periods_per_week: int
    available_rooms: list[int]
    name: str


subjects_info = [SubjectInfo(**subject) for subject in data["subjects"]]
