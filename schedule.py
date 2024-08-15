from itertools import product, pairwise
from ortools.sat.python import cp_model
from data import ScheduleData
from solution_callback import SolutionPrinter
from typing import Iterable


class Schedule:
    def __init__(
        self, optimize_distance: bool = False, use_alternating_weeks: bool = False
    ):
        self.data = self.load_schedule_data("real_info.json")
        self.use_alternating_weeks = use_alternating_weeks
        self.optimize_distance = optimize_distance

        self.model = cp_model.CpModel()
        self.setup_vars()
        self.add_constraints()

    def load_schedule_data(self, filepath: str):
        with open(filepath, encoding="utf-8") as f:
            return ScheduleData(f)

    def setup_vars(self):
        self.schedule_subjects = self.create_bool_vars(
            "d{0}p{1}s{2}", self.data.days, self.data.periods, self.data.subjects
        )
        self.schedule_rooms = self.create_bool_vars(
            "d{0}p{1}s{2}r{3}",
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.rooms,
        )
        self.schedule_teachers = self.create_bool_vars(
            "d{0}p{1}s{2}t{3}",
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.teachers,
        )

        if self.optimize_distance:
            self.setup_distance_vars()

        if self.use_alternating_weeks:
            self.setup_alternating_weeks_vars()

    def create_bool_vars(self, name_template: str, *dimensions: Iterable[int]):
        return {
            (indices): self.model.NewBoolVar(name_template.format(*indices))
            for indices in product(*dimensions)
        }

    def setup_distance_vars(self):
        self.schedule_rooms_by_classes = self.create_bool_vars(
            "c{0}d{1}p{2}r{3}",
            self.data.classes,
            self.data.days,
            self.data.periods,
            self.data.rooms,
        )
        self.schedule_room_distances = self.create_int_vars(
            "d{0}p{1}c{2}",
            0,
            1000000,
            self.data.days,
            range(self.data.num_periods - 1),
            self.data.classes,
        )
        self.class_day_distance_sum = self.create_int_vars(
            "d{0}c{1}", 0, 1000000, self.data.days, self.data.classes
        )

        self.max_distance = self.model.NewIntVar(0, 1000000, "distance_max")
        self.sum_distance = self.model.NewIntVar(0, 1000000, "distance_sum")

    def setup_alternating_weeks_vars(self):
        self.subjects_alignment = self.create_bool_vars(
            "d{0}p{1}s{2}",
            range(self.data.num_days // 2),
            self.data.periods,
            self.data.subjects,
        )

    def create_int_vars(
        self,
        name_template: str,
        min_value: int,
        max_value: int,
        *dimensions: Iterable[int]
    ):
        return {
            (indices): self.model.NewIntVar(
                min_value,
                max_value,
                name_template.format(*indices),
            )
            for indices in product(*dimensions)
        }

    def add_constraints(self):
        self.add_subject_constraints()
        self.add_class_constraints()
        self.add_teacher_constraints()
        self.add_room_constraints()

        if self.optimize_distance:
            self.add_room_distance_constraints()

        if self.use_alternating_weeks:
            self.add_alternating_week_constraints()

        print("done defining constraints")

    def add_subject_constraints(self):
        for s in self.data.subjects:
            periods_same_subject = [
                self.schedule_subjects[d, p, s]
                for d in self.data.days
                for p in self.data.periods
            ]
            self.model.Add(
                sum(periods_same_subject) == self.data.subjects_info[s].periods_per_week
            )

    def add_class_constraints(self):
        for c, d, p in product(self.data.classes, self.data.days, self.data.periods):
            subjects_same_class_period = [
                self.schedule_subjects[d, p, s]
                for s, subject in enumerate(self.data.subjects_info)
                if c in subject.classes
            ]
            self.model.AddAtMostOne(subjects_same_class_period)

    def add_teacher_constraints(self):
        for d, p, t in product(self.data.days, self.data.periods, self.data.teachers):
            subjects_same_teacher_period = [
                self.schedule_teachers[d, p, s, t] for s in self.data.subjects
            ]
            self.model.AddAtMostOne(subjects_same_teacher_period)

    def add_room_constraints(self):
        for d, p, r in product(self.data.days, self.data.periods, self.data.rooms):
            subjects_same_room_period = [
                self.schedule_rooms[d, p, s, r] for s in self.data.subjects
            ]
            self.model.AddAtMostOne(subjects_same_room_period)

        for d, s in product(self.data.days, self.data.subjects):
            periods_same_day_subject = [
                self.schedule_subjects[d, p, s] for p in self.data.periods
            ]
            self.model.AddAtMostOne(periods_same_day_subject)

        self.assign_rooms_and_teachers()

    def assign_rooms_and_teachers(self):
        for d, p, s in product(self.data.days, self.data.periods, self.data.subjects):
            self.model.Add(
                sum(
                    self.schedule_rooms[d, p, s, r]
                    for r in self.data.subjects_info[s].available_rooms
                )
                == self.schedule_subjects[d, p, s]
            )

            available_teachers = [
                self.schedule_teachers[d, p, s, t]
                for t in self.data.subjects_info[s].teachers
            ]
            all_teachers = [
                self.schedule_teachers[d, p, s, t] for t in self.data.teachers
            ]
            self.model.Add(
                sum(available_teachers)
                == self.data.subjects_info[s].teachers_per_period
            ).OnlyEnforceIf(self.schedule_subjects[d, p, s])
            self.model.Add(
                sum(all_teachers) == self.data.subjects_info[s].teachers_per_period
            ).OnlyEnforceIf(self.schedule_subjects[d, p, s])
            self.model.Add(sum(all_teachers) == 0).OnlyEnforceIf(
                self.schedule_subjects[d, p, s].Not()
            )

    def add_room_distance_constraints(self):
        self.assign_rooms_to_classes()
        self.assign_distances()
        self.calculate_distance_sums()
        self.minimize_max_distance_per_day()

    def assign_rooms_to_classes(self):
        for d, p, r, c in product(
            self.data.days, self.data.periods, self.data.rooms, self.data.classes
        ):
            subjects_of_class = [
                self.schedule_subjects[d, p, s]
                for s in self.data.subjects
                if c in self.data.subjects_info[s].classes
            ]
            for s in self.data.subjects:
                if c not in self.data.subjects_info[s].classes:
                    continue
                self.model.Add(
                    self.schedule_rooms_by_classes[c, d, p, r]
                    == self.schedule_rooms[d, p, s, r]
                ).OnlyEnforceIf(self.schedule_subjects[d, p, s])
            self.model.Add(
                self.schedule_rooms_by_classes[c, d, p, r] == 0
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
                self.schedule_room_distances[d, p1, c]
                == self.data.room_distances[r1][r2]
            ).OnlyEnforceIf(
                self.schedule_rooms_by_classes[c, d, p1, r1],
                self.schedule_rooms_by_classes[c, d, p2, r2],
            )

    def calculate_distance_sums(self):
        for d, c in product(self.data.days, self.data.classes):
            distance_sum = sum(
                self.schedule_room_distances[d, p, c]
                for p in range(self.data.num_periods - 1)
            )
            self.model.Add(self.class_day_distance_sum[d, c] == distance_sum)

        all_distances = [
            self.schedule_room_distances[d, p, c]
            for d in self.data.days
            for p in range(self.data.num_periods - 1)
            for c in self.data.classes
        ]
        self.model.Add(self.sum_distance == sum(all_distances))

    def minimize_max_distance_per_day(self):
        distances_per_day = [
            self.class_day_distance_sum[d, c]
            for d in self.data.days
            for c in self.data.classes
        ]
        self.model.AddMaxEquality(self.max_distance, distances_per_day)
        self.model.Minimize(self.max_distance)

    def add_alternating_week_constraints(self):
        for s in self.data.subjects:
            alignment_vars: list[cp_model.IntVar] = []
            for d, p in product(range(self.data.num_days // 2), self.data.periods):
                d2 = d + self.data.num_days // 2
                alignment_var = self.subjects_alignment[d, p, s]

                self.model.Add(alignment_var == 1).OnlyEnforceIf(
                    self.schedule_subjects[d, p, s],
                    self.schedule_subjects[d2, p, s],
                )

                self.model.Add(alignment_var == 0).OnlyEnforceIf(
                    self.schedule_subjects[d, p, s].Not(),
                    self.schedule_subjects[d2, p, s],
                )
                self.model.Add(alignment_var == 0).OnlyEnforceIf(
                    self.schedule_subjects[d, p, s],
                    self.schedule_subjects[d2, p, s].Not(),
                )
                self.model.Add(alignment_var == 0).OnlyEnforceIf(
                    self.schedule_subjects[d, p, s].Not(),
                    self.schedule_subjects[d2, p, s].Not(),
                )
                alignment_vars.append(alignment_var)
            num_pairs = self.data.subjects_info[s].periods_per_week // 2
            self.model.add(sum(alignment_vars) == num_pairs)

    def solve_and_print(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model, SolutionPrinter(self))
        print(status)
