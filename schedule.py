import asyncio
import json
from pathlib import Path
from typing import Any

import minizinc

from data import ScheduleData
from data_minizinc import minizinc_data
from utils import create_file


class Schedule:
    def __init__(self, schedule_data: ScheduleData):
        self.schedule_data = schedule_data
        self.data = minizinc_data(schedule_data)

        with create_file("generated/minizinc_data.json") as f:
            json.dump(self.data, f)

        self.solver = minizinc.Solver.lookup("cp-sat")
        self.model = minizinc.Model("model.mzn")
        self.instance = minizinc.Instance(self.solver, self.model)

        self.assign_data()

    def assign_data(self):
        for key, value in self.data.items():
            self.instance[key] = value

    def solve(self):
        asyncio.run(self._solve())

    async def _solve(self):
        async for result in self.instance.solutions(
            processes=8, intermediate_solutions=True
        ):
            if result.solution is not None:
                self.save_variables(result.solution.__dict__)
            print(result.statistics)
            print(result.status)

    def save_variables(self, obj: dict[str, Any]):
        output_file = Path("generated/variable_values.json")
        output_file.parent.mkdir(exist_ok=True, parents=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"input": self.schedule_data.to_json_object(), "output": obj}, f)
        print("saved variables")
