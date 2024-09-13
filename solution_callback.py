from pathlib import Path
from ortools.sat.python import cp_model
from typing import TYPE_CHECKING
import traceback
import json


if TYPE_CHECKING:
    from schedule import Schedule
    from schedule import IntVariableGroup


class SolutionCallback(cp_model.CpSolverSolutionCallback):
    def __init__(self, schedule: "Schedule"):
        super().__init__()
        self.schedule = schedule
        self.solution_count = 0

        self.variable_groups: dict[str, list[dict[str, int]]] = {}
        self.single_variables: dict[str, int] = {}

    def get_variable_group_values(self, var_group: "IntVariableGroup"):
        return [
            dict(zip(var_group.axes, key)) | {"value": self.Value(var)}
            for key, var in var_group.items()
        ]

    def get_variables_value(self):
        for name, group in self.schedule.variable_groups.items():
            self.variable_groups[name] = self.get_variable_group_values(group)

        for name, var in self.schedule.single_variables.items():
            self.single_variables[name] = self.Value(var)

    def save_variable_values(self):
        output_file = Path(f"generated/variable_values{self.solution_count}.json")
        output_file.parent.mkdir(exist_ok=True, parents=True)

        with open(output_file, "w", encoding="utf-8") as f:
            obj = {
                "variable_groups": self.variable_groups,
                "single_variables": self.single_variables,
            }
            json.dump(obj, f)
        print("saved variables")

    def on_solution_callback(self):
        try:
            self.solution_count += 1
            self.get_variables_value()
            self.save_variable_values()

            # self.print_solution()
        except Exception as e:
            traceback.print_exc()
            raise e

    # def print_solution(self):
    #     for c in self.schedule.data.classes:
    #         print(f"Class {c} Schedule:")
    #         for d in self.schedule.data.days:
    #             print(f"  Day {d}: ", end="")
    #             for p in self.schedule.data.periods:
    #                 for s in self.schedule.data.subjects:
    #                     if c not in self.schedule.data.subjects_info[s].classes:
    #                         continue
    #                     subject = self.variable_groups["schedule_subjects_values"][
    #                         d, p, s
    #                     ]

    #                     if not subject:
    #                         continue
    #                     subject_info = self.schedule.data.subjects_info[s]

    #                     room = None
    #                     for r in subject_info.available_rooms:
    #                         room_value = self.variable_groups["schedule_rooms_values"][
    #                             d, p, s, r
    #                         ]

    #                         if not room_value:
    #                             continue
    #                         room = r
    #                         break

    #                     teachers: list[int] = []
    #                     for t in subject_info.teachers:
    #                         teacher_value = self.variable_groups[
    #                             "schedule_teachers_values"
    #                         ][d, p, s, t]

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

    #                 if self.schedule.optimize_distance:
    #                     if p == self.schedule.data.num_periods - 1:
    #                         break
    #                     distance = self.variable_groups[
    #                         "schedule_room_distances_values"
    #                     ][d, p, c]

    #                     print(f"{distance}".ljust(4), end="")
    #             print()
    #     if self.schedule.optimize_distance:
    #         print(
    #             f"max distance per day: {self.value(self.schedule.single_variables['max_distance'])}"
    #         )
    #         print(
    #             f"sum distance: {self.value(self.schedule.single_variables['sum_distance'])}"
    #         )
