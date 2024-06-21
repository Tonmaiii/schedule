from itertools import product
from typing import Sequence
from ortools.sat.python import cp_model

from data import ScheduleData


class Schedule:
    def __init__(self):
        with open("info.json", encoding="utf-8") as f:
            self.data = ScheduleData(f)

        self.model = cp_model.CpModel()
        self.setup_vars()
        self.add_constraints()

    def add_constraints(self):
        # subjects in the same class cannot appear on the same period
        for c, d, p in product(self.data.classes, self.data.days, self.data.periods):
            subjects_same_class_period = (
                self.schedule_subjects[d, p, s]
                for s, subject in enumerate(self.data.subjects_info)
                if c in subject.classes
            )
            self.model.add_at_most_one(subjects_same_class_period)
 
        # each subject appears n times
        for s in self.data.subjects:
            periods_same_subject = (
                self.schedule_subjects[d, p, s]
                for d in self.data.days
                for p in self.data.periods
            )
            self.model.add(
                sum(periods_same_subject) == self.data.subjects_info[s].periods_per_week
            )

        # no same subjects on the same day
        for d, s in product(self.data.days, self.data.subjects):
            periods_same_day_subject = (
                self.schedule_subjects[d, p, s] for p in self.data.periods
            )
            self.model.add_at_most_one(periods_same_day_subject)

        # subjects with the same teacher cannot appear on the same period
        for d, p, t in product(self.data.days, self.data.periods, self.data.teachers):
            subjects_same_teacher_period = (
                self.schedule_subjects[d, p, s]
                for s, subject in enumerate(self.data.subjects_info)
                if t in subject.teachers
            )
            self.model.add_at_most_one(subjects_same_teacher_period)

    def setup_vars(self):
        self.schedule_subjects: dict[tuple[int, int, int], cp_model.IntVar] = {}
        for d, p, s in product(
            self.data.days,
            self.data.periods,
            self.data.subjects,
        ):
            self.schedule_subjects[d, p, s] = self.model.new_bool_var(f"d{d}p{p}s{s}")

    def solve_and_print(self):
        solver = cp_model.CpSolver()
        status = solver.solve(self.model)

        if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
            for c in self.data.classes:
                print(f"Class {c} Schedule:")
                for d in self.data.days:
                    print(f"  Day {d}: ", end="")
                    for p in self.data.periods:
                        for s in self.data.subjects:
                            if c not in self.data.subjects_info[s].classes:
                                continue
                            subject = solver.value(self.schedule_subjects[d, p, s])
                            if not subject:
                                continue
                            subject_info = self.data.subjects_info[s]
                            print(
                                f"{subject_info.name}:{subject_info.teachers}".ljust(
                                    16
                                ),
                                end="",
                            )
                            break
                        else:
                            print("".ljust(16), end="")
                    print()
        else:
            print("No solution found.")


if __name__ == "__main__":
    schedule = Schedule()
    schedule.solve_and_print()
