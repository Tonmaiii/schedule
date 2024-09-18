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
        output_file = Path("generated/variable_values.json")
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
            print(f"solution {self.solution_count}")
        except Exception as e:
            traceback.print_exc()
            raise e
