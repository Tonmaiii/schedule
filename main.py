from itertools import product
from typing import Sequence
from ortools.sat.python import cp_model

from info import ScheduleInfoJson


class Schedule:
    def __init__(self):
        with open("info_one_class.json", encoding="utf-8") as f:
            self.info = ScheduleInfoJson(f)

        self.model = cp_model.CpModel()

        schedule_subjects: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
        schedule_teachers: dict[tuple[int, int, int, int], cp_model.IntVar] = {}

        for c, d, p, s in self.info.product("classes", "days", "periods", "subjects"):
            schedule_subjects[c, d, p, s] = self.model.new_bool_var(f"{c},{d},{p},s{s}")

        for c, d, p, t in self.info.product("classes", "days", "periods", "teachers"):
            schedule_teachers[c, d, p, t] = self.model.new_bool_var(f"{c},{d},{p},t{t}")
