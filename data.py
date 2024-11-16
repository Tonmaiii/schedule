from dataclasses import asdict, dataclass, is_dataclass
from itertools import product
from typing import Any, Literal


@dataclass
class SubjectData:
    classes: list[int]
    periods_per_week: int
    teachers: list[int]
    teachers_per_period: int
    available_rooms: list[int]
    rooms_per_period: int
    name: str
    available_periods: list[list[int]]
    course: int | None


@dataclass
class TeacherData:
    name: str
    available_periods: list[list[int]]


@dataclass
class ClassData:
    name: str


@dataclass
class RoomData:
    name: str
    available_periods: list[list[int]]


@dataclass
class EqualTeacherDistribution:
    teachers: list[int]
    teachers_per_period: int
    type: Literal["equal"] = "equal"


@dataclass
class ManualTeacherDistribution:
    distribution: dict[int, int]
    type: Literal["manual"] = "manual"


@dataclass
class CourseData:
    name: str
    teacher_distribution: None | EqualTeacherDistribution | ManualTeacherDistribution
    subjects: list[int]


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
        self.num_courses = len(data["courses"])

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
                periods_per_week=s["periods_per_week"],
                teachers=s["teachers"],
                teachers_per_period=s["teachers_per_period"],
                available_rooms=s["available_rooms"],
                rooms_per_period=s["rooms_per_period"],
                name=s["name"],
                available_periods=s.get("available_periods")
                or self.default_available_periods(),
                course=s.get("course", None),
            )
            for s in data["subjects"]
        ]
        self.teachers_data = [
            TeacherData(
                name=t["name"],
                available_periods=t.get("available_periods")
                or self.default_available_periods(),
            )
            for t in data["teachers"]
        ]
        self.classes_data = [ClassData(name=c["name"]) for c in data["classes"]]
        self.rooms_data = [
            RoomData(
                name=r["name"],
                available_periods=r.get("available_periods")
                or self.default_available_periods(),
            )
            for r in data["rooms"]
        ]

        self.courses_data = [
            CourseData(
                name=q["name"],
                teacher_distribution=self.parse_teacher_distribution(
                    q.get("teacher_distribution", None)
                ),
                subjects=q["subjects"],
            )
            for q in data["courses"]
        ]

        self.room_distances: list[list[int]] = data.get("room_distances")

    def default_available_periods(self):
        return [list(p) for p in product(self.days, self.periods)]

    def parse_teacher_distribution(self, data: Any):
        if data is None:
            return None
        if data["type"] == "equal":
            return EqualTeacherDistribution(
                data["teachers"], data["teachers_per_period"]
            )
        if data["type"] == "manual":
            return ManualTeacherDistribution(
                {int(t): n for t, n in data["distribution"].items()}
            )
        raise ValueError(f"Unknown teacher distribution method: {repr(data['type'])}")

    def to_json_object(self):
        return to_json_compatible(
            {
                "config": self.config,
                "days": self.num_days,
                "periods": self.num_periods,
                "teachers": self.teachers_data,
                "classes": self.classes_data,
                "rooms": self.rooms_data,
                "room_distances": self.room_distances,
                "courses": self.courses_data,
                "subjects": self.subjects_data,
            }
        )


def to_json_compatible(data: Any) -> Any:
    if is_dataclass(data) and not isinstance(data, type):
        return asdict(data)
    if isinstance(data, list):
        return [to_json_compatible(item) for item in data]
    if isinstance(data, dict):
        return {key: to_json_compatible(value) for key, value in data.items()}
    return data


if __name__ == "__main__":
    import json

    with open("input/data.json", encoding="utf-8") as f:
        json_data = json.load(f)

    data = ScheduleData(json_data)
    data_parsed = data.to_json_object()

    with open("generated/data_parsed.json", "w", encoding="utf-8") as f:
        json.dump(data_parsed, f, ensure_ascii=False)
