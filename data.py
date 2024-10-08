from dataclasses import dataclass
from typing import Any
from itertools import product


@dataclass
class SubjectData:
    classes: list[int]
    teachers: list[int]
    periods_per_week: int
    teachers_per_period: int
    available_rooms: list[int]
    name: str
    available_periods: list[tuple[int, int]]


@dataclass
class TeachersData:
    name: str


@dataclass
class ClassesData:
    name: str


@dataclass
class RoomsData:
    name: str


@dataclass
class ScheduleConfig:
    use_alternating_weeks: bool = False
    optimize_distance: bool = False
    schedule_rooms: bool = True


class ScheduleData:
    def __init__(self, data: Any):
        self.num_days: int = data["days"]
        self.num_periods: int = data["periods"]
        self.num_teachers: int = len(data["teachers"])
        self.num_classes: int = len(data["classes"])
        self.num_rooms: int = len(data["rooms"])
        self.num_subjects = len(data["subjects"])

        self.days = range(self.num_days)
        self.periods = range(self.num_periods)
        self.teachers = range(self.num_teachers)
        self.classes = range(self.num_classes)
        self.rooms = range(self.num_rooms)
        self.subjects = range(self.num_subjects)

        self.config = ScheduleConfig(**data["config"])

        self.subjects_data = [
            SubjectData(
                classes=s["classes"],
                teachers=s["teachers"],
                periods_per_week=s["periods_per_week"],
                teachers_per_period=s["teachers_per_period"],
                available_rooms=s["available_rooms"],
                name=s["name"],
                available_periods=s.get("available_periods")
                or self.default_available_periods(),
            )
            for s in data["subjects"]
        ]
        self.teachers_data = [TeachersData(name=t["name"]) for t in data["teachers"]]
        self.classes_data = [ClassesData(name=c["name"]) for c in data["classes"]]
        self.rooms_data = [RoomsData(name=r["name"]) for r in data["rooms"]]

        self.room_distances: list[list[int]] = data.get("room_distances")

    def default_available_periods(self):
        return list(product(self.days, self.periods))
