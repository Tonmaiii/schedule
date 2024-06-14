import json
from dataclasses import dataclass
from itertools import product
import io
from typing import Literal, Sequence


@dataclass
class SubjectInfo:
    classes: list[int]
    teachers: list[int]
    periods_per_week: int
    available_rooms: list[int]
    name: str


class ScheduleInfoJson:
    def __init__(self, f: io.IOBase):
        data = json.load(f)

        self.days: int = data["days"]
        self.periods: int = data["periods"]
        self.teachers: int = data["teachers"]
        self.classes: int = data["classes"]
        self.rooms: int = data["rooms"]
        self.subjects = len(data["subjects"])

        self.subjects_info = [SubjectInfo(**subject) for subject in data["subjects"]]

        self.ranges_map = {
            "days": range(self.days),
            "periods": range(self.periods),
            "teachers": range(self.teachers),
            "classes": range(self.classes),
            "rooms": range(self.rooms),
            "subjects": range(self.subjects),
        }

    def product(
        self,
        *elements: Literal[
            "days", "periods", "teachers", "classes", "rooms", "subjects"
        ],
    ):
        lists = [self.ranges_map[element] for element in elements]
        return product(*lists)
