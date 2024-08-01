from itertools import product, pairwise
from ortools.sat.python import cp_model

from data import ScheduleData
from solution_callback import PrintSolutions


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

        # subjects with the same teacher cannot appear on the same period
        for d, p, t in product(self.data.days, self.data.periods, self.data.teachers):
            subjects_same_teacher_period = (
                self.schedule_teachers[d, p, s, t] for s in self.data.subjects
            )
            self.model.add_at_most_one(subjects_same_teacher_period)

        # subjects with the same room cannot appear on the same period
        for d, p, r in product(self.data.days, self.data.periods, self.data.rooms):
            subjects_same_room_period = (
                self.schedule_rooms[d, p, s, r] for s in self.data.subjects
            )
            self.model.add_at_most_one(subjects_same_room_period)

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

        # each subject chooses a room
        for d, p, s in product(self.data.days, self.data.periods, self.data.subjects):
            available_rooms = (
                self.schedule_rooms[d, p, s, r]
                for r in self.data.subjects_info[s].available_rooms
            )
            self.model.add(sum(available_rooms) == self.schedule_subjects[d, p, s])

        # each subject chooses a teacher
        for d, p, s in product(self.data.days, self.data.periods, self.data.subjects):
            available_teachers = (
                self.schedule_teachers[d, p, s, t]
                for t in self.data.subjects_info[s].teachers
            )
            self.model.add(
                sum(available_teachers)
                == self.data.subjects_info[s].teachers_per_period
            ).only_enforce_if(self.schedule_subjects[d, p, s])

        # no same subjects on the same day
        for d, s in product(self.data.days, self.data.subjects):
            periods_same_day_subject = (
                self.schedule_subjects[d, p, s] for p in self.data.periods
            )
            self.model.add_at_most_one(periods_same_day_subject)

        # assign rooms on class schedule
        for d, p, s, r in product(
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.rooms,
        ):
            for c in self.data.subjects_info[s].classes:
                self.model.add(
                    self.schedule_rooms_by_classes[c, d, p, r]
                    == self.schedule_rooms[d, p, s, r]
                ).only_enforce_if(self.schedule_subjects_by_classes[c, d, p, s])

        # assign distances
        for d, [p1, p2], c, r1, r2 in product(
            self.data.days,
            pairwise(self.data.periods),
            self.data.classes,
            self.data.rooms,
            self.data.rooms,
        ):
            self.model.add(
                self.schedule_room_distances[d, p1, c]
                == self.data.room_distances[r1][r2]
            ).only_enforce_if(
                self.schedule_rooms_by_classes[c, d, p1, r1],
                self.schedule_rooms_by_classes[c, d, p2, r2],
            )

        # minimize distance
        all_distances = (
            self.schedule_room_distances[d, p, c]
            for d, p, c in product(
                self.data.days,
                range(self.data.num_periods - 1),
                self.data.classes,
            )
        )
        self.model.add(self.sum_distance == sum(all_distances))

        print("done defining constraints")

    def setup_vars(self):
        self.schedule_subjects: dict[tuple[int, int, int], cp_model.IntVar] = {}
        for d, p, s in product(
            self.data.days,
            self.data.periods,
            self.data.subjects,
        ):
            self.schedule_subjects[d, p, s] = self.model.new_bool_var(f"d{d}p{p}s{s}")

        self.schedule_rooms: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
        for d, p, s, r in product(
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.rooms,
        ):
            self.schedule_rooms[d, p, s, r] = self.model.new_bool_var(
                f"d{d}p{p}s{s}r{r}"
            )

        self.schedule_teachers: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
        for d, p, s, t in product(
            self.data.days,
            self.data.periods,
            self.data.subjects,
            self.data.teachers,
        ):
            self.schedule_teachers[d, p, s, t] = self.model.new_bool_var(
                f"d{d}p{p}s{s}t{t}"
            )

        self.schedule_subjects_by_classes: dict[
            tuple[int, int, int, int], cp_model.IntVar
        ] = {}
        for d, p, s in product(
            self.data.days,
            self.data.periods,
            self.data.subjects,
        ):
            for c in self.data.subjects_info[s].classes:
                self.schedule_subjects_by_classes[c, d, p, s] = self.schedule_subjects[
                    d, p, s
                ]

        self.schedule_rooms_by_classes: dict[
            tuple[int, int, int, int], cp_model.IntVar
        ] = {}
        for c, d, p, r in product(
            self.data.classes,
            self.data.days,
            self.data.periods,
            self.data.rooms,
        ):
            self.schedule_rooms_by_classes[c, d, p, r] = self.model.new_bool_var(
                f"c{c}d{d}p{p}r{r}"
            )

        self.schedule_room_distances: dict[tuple[int, int, int], cp_model.IntVar] = {}
        for d, p, c in product(
            self.data.days,
            range(self.data.num_periods - 1),
            self.data.classes,
        ):
            self.schedule_room_distances[d, p, c] = self.model.new_int_var(
                0, 1000000, f"d{d}p{p}c{c}"
            )

        self.sum_distance = self.model.new_int_var(0, 1000000, "distance_sum")

    def solve_and_print(self):
        self.model.minimize(self.sum_distance)
        solver = cp_model.CpSolver()
        # solver.parameters.max_time_in_seconds = 10.0
        status = solver.solve(self.model, PrintSolutions(self))

        # if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        #     for c in self.data.classes:
        #         print(f"Class {c} Schedule:")
        #         for d in self.data.days:
        #             print(f"  Day {d}: ", end="")
        #             for p in self.data.periods:
        #                 for s in self.data.subjects:
        #                     if c not in self.data.subjects_info[s].classes:
        #                         continue
        #                     subject = solver.value(self.schedule_subjects[d, p, s])
        #                     assert subject == solver.value(
        #                         self.schedule_subjects_by_classes[c, d, p, s]
        #                     )
        #                     if not subject:
        #                         continue
        #                     subject_info = self.data.subjects_info[s]

        #                     room = None
        #                     for r in subject_info.available_rooms:
        #                         room_value = solver.value(
        #                             self.schedule_rooms[d, p, s, r]
        #                         )
        #                         assert room_value == solver.value(
        #                             self.schedule_rooms_by_classes[c, d, p, r]
        #                         )

        #                         if not room_value:
        #                             continue
        #                         room = r
        #                         break

        #                     teachers: list[int] = []
        #                     for t in subject_info.teachers:
        #                         teacher_value = solver.value(
        #                             self.schedule_teachers[d, p, s, t]
        #                         )
        #                         if not teacher_value:
        #                             continue
        #                         teachers.append(t)

        #                     print(
        #                         f"{subject_info.name}:{teachers}:{room}".ljust(18),
        #                         end="",
        #                     )
        #                     break
        #                 else:
        #                     print("".ljust(18), end="")

        #                 if p == self.data.num_periods - 1:
        #                     break
        #                 distance = solver.value(self.schedule_room_distances[d, p, c])
        #                 print(f"{distance}".ljust(4), end="")
        #             print()
        #     print(f"sum distance: {solver.value(self.sum_distance)}")
        # else:
        #     print("No solution found.")
