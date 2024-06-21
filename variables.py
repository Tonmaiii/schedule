from collections import defaultdict
from itertools import product
from data import ScheduleData
from ortools.sat.python import cp_model


class SubjectScheduleVars:
    def __init__(self, model: cp_model.CpModel, data: ScheduleData):
        self.schedule: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
        self.data = data

        for c, d, p, s in product(
            self.data.classes, self.data.days, self.data.periods, self.data.subjects
        ):
            self.schedule[c, d, p, s] = model.new_bool_var(f"c{c}d{d}p{p}s{s}")

    def __getitem__(self, index: tuple[int, int, int, int]):
        return self.schedule[index]

    def groupings(
        self,
        classes: bool = False,
        days: bool = False,
        periods: bool = False,
        subjects: bool = False,
    ):
        indices = product(
            self.data.classes, self.data.days, self.data.periods, self.data.subjects
        )

        grouped: defaultdict[tuple[int, ...], list[cp_model.IntVar]] = defaultdict(list)
        constant_indices = tuple(
            i for i, c in enumerate((classes, days, periods, subjects)) if c
        )

        for index in indices:
            group_key = tuple(index[c] for c in constant_indices)
            grouped[group_key].append(self.schedule[index])

        return list(grouped.values())


class TeacherScheduleVars:
    def __init__(self, model: cp_model.CpModel, data: ScheduleData):
        self.schedule: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
        self.data = data

        for c, d, p, t in product(data.classes, data.days, data.periods, data.teachers):
            self.schedule[c, d, p, t] = model.new_bool_var(f"c{c}d{d}p{p}t{t}")

    def __getitem__(self, index: tuple[int, int, int, int]):
        return self.schedule[index]

    def groupings(
        self,
        classes: bool = False,
        days: bool = False,
        periods: bool = False,
        teachers: bool = False,
    ):
        indices = product(
            self.data.classes, self.data.days, self.data.periods, self.data.teachers
        )

        grouped: defaultdict[tuple[int, ...], list[cp_model.IntVar]] = defaultdict(list)
        constant_indices = tuple(
            i for i, c in enumerate((classes, days, periods, teachers)) if c
        )

        for index in indices:
            group_key = tuple(index[c] for c in constant_indices)
            grouped[group_key].append(self.schedule[index])

        return list(grouped.values())
