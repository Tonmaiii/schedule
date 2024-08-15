from ortools.sat.python import cp_model
from typing import TypeVar
from typing import TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from schedule import Schedule


VariableGroup = dict[tuple[int, ...], int]


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, schedule: "Schedule"):
        super().__init__()
        self.schedule = schedule
        self.solution_count = 0

        self.schedule_subjects_values: VariableGroup = {}
        self.schedule_rooms_values: VariableGroup = {}
        self.schedule_teachers_values: VariableGroup = {}
        self.schedule_rooms_by_classes_values: VariableGroup = {}
        self.schedule_room_distances_values: VariableGroup = {}
        self.class_day_distance_sum_values: VariableGroup = {}
        self.max_distance_value = 0
        self.sum_distance_value = 0

    def get_variable_values(self, vars_dict: dict[tuple[int, ...], cp_model.IntVar]):
        return {key: self.Value(var) for key, var in vars_dict.items()}

    def on_solution_callback(self):
        self.solution_count += 1

        self.schedule_subjects_values = self.get_variable_values(
            self.schedule.schedule_subjects
        )
        self.schedule_rooms_values = self.get_variable_values(
            self.schedule.schedule_rooms
        )
        self.schedule_teachers_values = self.get_variable_values(
            self.schedule.schedule_teachers
        )

        if self.schedule.optimize_distance:
            self.schedule_rooms_by_classes_values = self.get_variable_values(
                self.schedule.schedule_rooms_by_classes
            )
            self.schedule_room_distances_values = self.get_variable_values(
                self.schedule.schedule_room_distances
            )
            self.class_day_distance_sum_values = self.get_variable_values(
                self.schedule.class_day_distance_sum
            )
            self.max_distance_value = self.Value(self.schedule.max_distance)
            self.sum_distance_value = self.Value(self.schedule.sum_distance)

        self.print_solution()

    def print_solution(self):
        try:
            for c in self.schedule.data.classes:
                print(f"Class {c} Schedule:")
                for d in self.schedule.data.days:
                    print(f"  Day {d}: ", end="")
                    for p in self.schedule.data.periods:
                        for s in self.schedule.data.subjects:
                            if c not in self.schedule.data.subjects_info[s].classes:
                                continue
                            subject = self.schedule_subjects_values[d, p, s]

                            if not subject:
                                continue
                            subject_info = self.schedule.data.subjects_info[s]

                            room = None
                            for r in subject_info.available_rooms:
                                room_value = self.schedule_rooms_values[d, p, s, r]

                                if not room_value:
                                    continue
                                room = r
                                break

                            teachers: list[int] = []
                            for t in subject_info.teachers:
                                teacher_value = self.schedule_teachers_values[
                                    d, p, s, t
                                ]

                                if not teacher_value:
                                    continue
                                teachers.append(t)

                            print(
                                f"{subject_info.name}:{teachers}:{room}".ljust(18),
                                end="",
                            )
                            break
                        else:
                            print("".ljust(18), end="")

                        if self.schedule.optimize_distance:
                            if p == self.schedule.data.num_periods - 1:
                                break
                            distance = self.schedule_room_distances_values[d, p, c]

                            print(f"{distance}".ljust(4), end="")
                    print()
            if self.schedule.optimize_distance:
                print(f"max distance per day: {self.value(self.schedule.max_distance)}")
                print(f"sum distance: {self.value(self.schedule.sum_distance)}")
        except Exception as e:
            traceback.print_exc()
            raise e
