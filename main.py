from itertools import product
from typing import Sequence
from ortools.sat.python import cp_model

from info import ScheduleDataJson


class Schedule:
    def __init__(self):
        with open("info_one_class.json", encoding="utf-8") as f:
            self.data = ScheduleDataJson(f)

        self.model = cp_model.CpModel()
        self.setup_vars()

    def add_constraints(self):
        for group in self.data.groupings(("c", "d", "p", "s"), ("s",)):
            self.model.add_at_most_one(self.schedule_subjects[index] for index in group)

    def setup_vars(self):
        self.schedule_subjects: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
        self.schedule_teachers: dict[tuple[int, int, int, int], cp_model.IntVar] = {}

        for c, d, p, s in self.data.combinations("c", "d", "p", "s"):
            self.schedule_subjects[c, d, p, s] = self.model.new_bool_var(
                f"{c},{d},{p},s{s}"
            )

        for c, d, p, t in self.data.combinations("c", "d", "p", "t"):
            self.schedule_teachers[c, d, p, t] = self.model.new_bool_var(
                f"{c},{d},{p},t{t}"
            )


if __name__ == "__main__":
    Schedule()
