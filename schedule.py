import json
from itertools import pairwise, product
from typing import Sequence, Type

from ortools.sat.python import cp_model

from data import ScheduleData
from solution_callback import SolutionCallback


class IntVariableGroup(dict[tuple[int, ...], cp_model.IntVar]):
    def __init__(
        self,
        model: cp_model.CpModel,
        axes: Sequence[str],
        min_value: int,
        max_value: int,
        *dimensions: Sequence[int],
    ):
        super().__init__()
        self.axes = axes
        for indices in product(*dimensions):
            self.__setitem__(
                indices,
                model.NewIntVar(
                    min_value,
                    max_value,
                    "".join(f"{name}{value}" for name, value in zip(axes, indices)),
                ),
            )


class BoolVariableGroup(IntVariableGroup):
    def __init__(
        self, model: cp_model.CpModel, axes: Sequence[str], *dimensions: Sequence[int]
    ):
        super().__init__(model, axes, 0, 1, *dimensions)


class Schedule:
    def __init__(self):
        self.data = self.load_schedule_data("input/real_info.json")
        self.variable_groups: dict[str, IntVariableGroup] = {}
        self.single_variables: dict[str, cp_model.IntVar] = {}

        self.model = cp_model.CpModel()
        self.setup_vars()
        self.add_constraints()

    def load_schedule_data(self, filepath: str):
        with open(filepath, encoding="utf-8") as f:
            return ScheduleData(json.load(f))

    def setup_vars(self):
        self.create_bool_vars(
            "schedule_subjects",
            "dps",
            self.data.days,
            self.data.periods,
            self.data.subjects,
        )
        self.create_bool_vars(
            "schedule_rooms",
            "dpsr",
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.rooms,
        )
        self.create_bool_vars(
            "schedule_teachers",
            "dpst",
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.teachers,
        )
        self.create_bool_vars(
            "teacher_assignments",
            "st",
            self.data.subjects,
            self.data.teachers,
        )

        if self.data.config.schedule_rooms:
            self.create_bool_vars(
                "room_assignments",
                "sr",
                self.data.subjects,
                self.data.rooms,
            )

        if self.data.config.optimize_distance:
            self.setup_distance_vars()

        if self.data.config.use_alternating_weeks:
            self.setup_alternating_weeks_vars()

    def setup_distance_vars(self):
        self.create_bool_vars(
            "schedule_rooms_with_distance_by_classes",
            "cdpr",
            self.data.classes,
            self.data.days,
            self.data.periods,
            self.data.rooms,
        )
        self.create_int_vars(
            "schedule_room_distances",
            "dpc",
            0,
            1000000,
            self.data.days,
            range(self.data.num_periods - 1),
            self.data.classes,
        )
        self.create_int_vars(
            "class_day_distance_sum",
            "dc",
            0,
            1000000,
            self.data.days,
            self.data.classes,
        )

        self.single_variables["max_distance"] = self.model.NewIntVar(
            0, 1000000, "distance_max"
        )
        self.single_variables["sum_distance"] = self.model.NewIntVar(
            0, 1000000, "distance_sum"
        )

    def setup_alternating_weeks_vars(self):
        self.create_bool_vars(
            "subjects_alignment",
            "dps",
            range(self.data.num_days // 2),
            self.data.periods,
            self.data.subjects,
        )

    def create_int_vars(
        self,
        name: str,
        axes: Sequence[str],
        min_value: int,
        max_value: int,
        *dimensions: Sequence[int],
    ):
        self.variable_groups[name] = IntVariableGroup(
            self.model, axes, min_value, max_value, *dimensions
        )

    def create_bool_vars(
        self,
        name: str,
        axes: Sequence[str],
        *dimensions: Sequence[int],
    ):
        self.variable_groups[name] = BoolVariableGroup(self.model, axes, *dimensions)

    def add_constraints(self):
        self.add_subject_constraints()
        print("added subject constraints")
        self.add_class_constraints()
        print("added class constraints")

        if self.data.config.schedule_rooms:
            self.add_room_constraints()
            print("added room constraints")
            self.assign_rooms()
            print("added rooms assignment constraints")

        self.add_teacher_constraints()
        print("added teacher constraints")
        self.assign_teachers()
        print("added teachers assignment constraints")
        self.add_period_constraints()
        print("added periods constraints")

        if self.data.config.optimize_distance:
            self.add_room_distance_constraints()
            print("added distance constraints")

        if self.data.config.use_alternating_weeks:
            self.add_alternating_week_constraints()
            print("added alternating week constraints")

        print("done defining constraints")

    def add_subject_constraints(self):
        # Subject appears in n periods per week
        for s in self.data.subjects:
            periods_same_subject = [
                self.variable_groups["schedule_subjects"][d, p, s]
                for d in self.data.days
                for p in self.data.periods
            ]
            self.model.Add(
                sum(periods_same_subject) == self.data.subjects_data[s].periods_per_week
            )

        self.one_period_per_day()

    def one_period_per_day(self):
        for d, s in product(self.data.days, self.data.subjects):
            periods_same_day_subject = [
                self.variable_groups["schedule_subjects"][d, p, s]
                for p in self.data.periods
            ]
            self.model.AddAtMostOne(periods_same_day_subject)

    def add_class_constraints(self):
        # At most one subject is scheduled at the same time for that class
        for c, d, p in product(self.data.classes, self.data.days, self.data.periods):
            subjects_same_class_period = [
                self.variable_groups["schedule_subjects"][d, p, s]
                for s, subject in enumerate(self.data.subjects_data)
                if c in subject.classes
            ]
            self.model.AddAtMostOne(subjects_same_class_period)

    def add_teacher_constraints(self):
        # Each teacher is assigned to at most one subject per period
        for d, p, t in product(self.data.days, self.data.periods, self.data.teachers):
            subjects_same_teacher_period = [
                self.variable_groups["schedule_teachers"][d, p, s, t]
                for s in self.data.subjects
            ]
            if [d, p] not in self.data.teachers_data[t].available_periods:
                self.model.add(sum(subjects_same_teacher_period) == 0)
                continue

            self.model.AddAtMostOne(subjects_same_teacher_period)

    def add_room_constraints(self):
        # Each room is assigned to at most one subject per period
        for d, p, r in product(self.data.days, self.data.periods, self.data.rooms):
            subjects_same_room_period = [
                self.variable_groups["schedule_rooms"][d, p, s, r]
                for s in self.data.subjects
            ]
            if [d, p] not in self.data.rooms_data[r].available_periods:
                self.model.add(sum(subjects_same_room_period) == 0)
                continue

            self.model.AddAtMostOne(subjects_same_room_period)

    def assign_teachers(self):
        for s in self.data.subjects:
            available_teachers = [
                self.variable_groups["teacher_assignments"][s, t]
                for t in self.data.subjects_data[s].teachers
            ]
            all_teachers = [
                self.variable_groups["teacher_assignments"][s, t]
                for t in self.data.teachers
            ]
            self.model.Add(
                sum(available_teachers)
                == self.data.subjects_data[s].teachers_per_period
            )
            self.model.Add(
                sum(all_teachers) == self.data.subjects_data[s].teachers_per_period
            )

            for d, p, t in product(
                self.data.days,
                self.data.periods,
                self.data.teachers,
            ):
                self.model.Add(
                    self.variable_groups["schedule_teachers"][d, p, s, t]
                    <= self.variable_groups["teacher_assignments"][s, t]
                )

        for d, p, s, t in product(
            self.data.days, self.data.periods, self.data.subjects, self.data.teachers
        ):
            self.model.AddMultiplicationEquality(
                self.variable_groups["schedule_teachers"][d, p, s, t],
                [
                    self.variable_groups["teacher_assignments"][s, t],
                    self.variable_groups["schedule_subjects"][d, p, s],
                ],
            )

    def assign_rooms(self):
        for s in self.data.subjects:
            available_rooms = [
                self.variable_groups["room_assignments"][s, r]
                for r in self.data.subjects_data[s].available_rooms
            ]
            all_rooms = [
                self.variable_groups["room_assignments"][s, r] for r in self.data.rooms
            ]
            self.model.Add(
                sum(available_rooms) == self.data.subjects_data[s].rooms_per_period
            )
            self.model.Add(
                sum(all_rooms) == self.data.subjects_data[s].rooms_per_period
            )

            for d, p, r in product(
                self.data.days,
                self.data.periods,
                self.data.rooms,
            ):
                self.model.Add(
                    self.variable_groups["schedule_rooms"][d, p, s, r]
                    <= self.variable_groups["room_assignments"][s, r]
                )

        for d, p, s, r in product(
            self.data.days, self.data.periods, self.data.subjects, self.data.rooms
        ):
            self.model.AddMultiplicationEquality(
                self.variable_groups["schedule_rooms"][d, p, s, r],
                [
                    self.variable_groups["room_assignments"][s, r],
                    self.variable_groups["schedule_subjects"][d, p, s],
                ],
            )

    def add_period_constraints(self):
        for d, p, s in product(self.data.days, self.data.periods, self.data.subjects):
            if [d, p] not in self.data.subjects_data[s].available_periods:
                self.model.add(self.variable_groups["schedule_subjects"][d, p, s] == 0)

    def add_room_distance_constraints(self):
        self.assign_rooms_with_distance_by_classes()
        self.assign_distances()
        self.calculate_distance_sums()
        self.minimize_max_distance_per_day()

    def assign_rooms_with_distance_by_classes(self):
        # Assigning rooms by classes for subjects with only one room per period
        for d, p, r, c in product(
            self.data.days, self.data.periods, self.data.rooms, self.data.classes
        ):
            subjects_of_class = [
                self.variable_groups["schedule_subjects"][d, p, s]
                for s in self.data.subjects
                if c in self.data.subjects_data[s].classes
            ]
            for s in self.data.subjects:
                if c not in self.data.subjects_data[s].classes:
                    continue
                if self.data.subjects_data[s].rooms_per_period != 1:
                    continue
                self.model.Add(
                    self.variable_groups["schedule_rooms_with_distance_by_classes"][
                        c, d, p, r
                    ]
                    == self.variable_groups["schedule_rooms"][d, p, s, r]
                ).OnlyEnforceIf(self.variable_groups["schedule_subjects"][d, p, s])
            self.model.Add(
                self.variable_groups["schedule_rooms_with_distance_by_classes"][
                    c, d, p, r
                ]
                == 0
            ).OnlyEnforceIf([var.Not() for var in subjects_of_class])

    def assign_distances(self):
        for d, (p1, p2), c, r1, r2 in product(
            self.data.days,
            pairwise(self.data.periods),
            self.data.classes,
            self.data.rooms,
            self.data.rooms,
        ):
            self.model.Add(
                self.variable_groups["schedule_room_distances"][d, p1, c]
                == self.data.room_distances[r1][r2]
            ).OnlyEnforceIf(
                self.variable_groups["schedule_rooms_with_distance_by_classes"][
                    c, d, p1, r1
                ],
                self.variable_groups["schedule_rooms_with_distance_by_classes"][
                    c, d, p2, r2
                ],
            )

    def calculate_distance_sums(self):
        for d, c in product(self.data.days, self.data.classes):
            distance_sum = sum(
                self.variable_groups["schedule_room_distances"][d, p, c]
                for p in range(self.data.num_periods - 1)
            )
            self.model.Add(
                self.variable_groups["class_day_distance_sum"][d, c] == distance_sum
            )

        all_distances = [
            self.variable_groups["schedule_room_distances"][d, p, c]
            for d in self.data.days
            for p in range(self.data.num_periods - 1)
            for c in self.data.classes
        ]
        self.model.Add(self.single_variables["sum_distance"] == sum(all_distances))

    def minimize_max_distance_per_day(self):
        distances_per_day = [
            self.variable_groups["class_day_distance_sum"][d, c]
            for d in self.data.days
            for c in self.data.classes
        ]
        self.model.AddMaxEquality(
            self.single_variables["max_distance"], distances_per_day
        )
        self.model.Minimize(self.single_variables["max_distance"])

    def add_alternating_week_constraints(self):
        for s in self.data.subjects:
            alignment_vars: list[cp_model.IntVar] = []
            for d, p in product(range(self.data.num_days // 2), self.data.periods):
                d2 = d + self.data.num_days // 2
                alignment_var = self.variable_groups["subjects_alignment"][d, p, s]

                self.model.AddMinEquality(
                    alignment_var,
                    (
                        self.variable_groups["schedule_subjects"][d, p, s],
                        self.variable_groups["schedule_subjects"][d2, p, s],
                    ),
                )

                alignment_vars.append(alignment_var)
            num_pairs = self.data.subjects_data[s].periods_per_week // 2
            self.model.add(sum(alignment_vars) == num_pairs)

    def solve(self):
        solver = cp_model.CpSolver()
        # solver.parameters.max_time_in_seconds = 60
        solver.parameters.num_search_workers = 8
        solution_callback = SolutionCallback(self)
        status: int = solver.Solve(self.model, solution_callback)  # type: ignore

        print(solver.ResponseStats())

        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            solution_callback.save_variable_values()
        else:
            print("no solution")
