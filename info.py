from collections import defaultdict
from itertools import product
import json
from dataclasses import dataclass
import io
from typing import Literal, Sequence


@dataclass
class SubjectData:
    classes: list[int]
    teachers: list[int]
    periods_per_week: int
    available_rooms: list[int]
    name: str


class ScheduleDataJson:
    var_letter = Literal["d", "p", "t", "c", "r", "s"]

    def __init__(self, f: io.IOBase):
        data = json.load(f)

        self.num_days: int = data["days"]
        self.num_periods: int = data["periods"]
        self.num_teachers: int = data["teachers"]
        self.num_classes: int = data["classes"]
        self.num_rooms: int = data["rooms"]
        self.num_subjects = len(data["subjects"])

        self.subjects_info = [SubjectData(**subject) for subject in data["subjects"]]

        # self.days = range(self.num_days)
        # self.periods = range(self.num_periods)
        # self.teachers = range(self.num_teachers)
        # self.classes = range(self.num_classes)
        # self.rooms = range(self.num_rooms)
        # self.subjects = range(self.num_subjects)
        self.var_ranges: dict[ScheduleDataJson.var_letter, range] = {
            "d": range(self.num_days),
            "p": range(self.num_periods),
            "t": range(self.num_teachers),
            "c": range(self.num_classes),
            "r": range(self.num_rooms),
            "s": range(self.num_subjects),
        }

    def groupings(
        self, order: Sequence[var_letter], group_by: Sequence[var_letter] = tuple()
    ):
        all_combinations = tuple(product(*(self.var_ranges[var] for var in order)))

        grouped: defaultdict[tuple[int, ...], list[tuple[int, ...]]] = defaultdict(list)
        constant_indices = {var: order.index(var) for var in group_by}

        for combo in all_combinations:
            group_key = tuple(combo[constant_indices[var]] for var in group_by)
            grouped[group_key].append(combo)

        return tuple(grouped.values())

    def combinations(self, *order: var_letter):
        return tuple(product(*(self.var_ranges[var] for var in order)))
