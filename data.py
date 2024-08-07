import json
from dataclasses import dataclass
import io


@dataclass
class SubjectData:
    classes: list[int]
    teachers: list[int]
    periods_per_week: int
    teachers_per_period: int
    available_rooms: list[int]
    name: str


class ScheduleData:
    def __init__(self, f: io.IOBase):
        data = json.load(f)

        self.num_days: int = data["days"]
        self.num_periods: int = data["periods"]
        self.num_teachers: int = data["teachers"]
        self.num_classes: int = data["classes"]
        self.num_rooms: int = data["rooms"]
        self.num_subjects = len(data["subjects"])

        self.days = range(self.num_days)
        self.periods = range(self.num_periods)
        self.teachers = range(self.num_teachers)
        self.classes = range(self.num_classes)
        self.rooms = range(self.num_rooms)
        self.subjects = range(self.num_subjects)

        self.subjects_info = [
            SubjectData(
                classes=subject["classes"],
                teachers=subject["teachers"],
                periods_per_week=subject["periods_per_week"],
                teachers_per_period=subject["teachers_per_period"],
                available_rooms=subject["available_rooms"],
                name=subject["name"],
            )
            for subject in data["subjects"]
        ]
        self.room_distances: list[list[int]] = data["room_distances"]
