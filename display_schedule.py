from data import ScheduleData
from dataclasses import dataclass
import json
import csv
from pathlib import Path
from typing import Any


@dataclass
class SaveSchedule:
    data: ScheduleData
    variable_groups: dict[str, list[dict[str, int]]]
    single_variables: dict[str, int]

    def save_schedule(self, path: str):
        output_file = Path(path)
        output_file.parent.mkdir(exist_ok=True, parents=True)

        with open(output_file, "w", encoding="utf-8") as f:
            writer = csv.writer(f, lineterminator="\n")

            header = ["Day", "Class"]

            for p in self.data.periods:
                header.append(f"{p+1}A")
                header.append(f"{p+1}B")

            writer.writerow(header)

            for d in range(self.data.num_days // 2):
                for c in self.data.classes:
                    row: list[Any] = [d + 1, c + 1]
                    for p in self.data.periods:
                        p1 = self.get_period_info(c, d, p)
                        p2 = self.get_period_info(c, d + self.data.num_days // 2, p)

                        if p1 is None:
                            row.append("-")
                        else:
                            row.append(
                                f'{self.data.subjects_info[p1["s"]].name}\n{[self.data.teachers_mapping[t] for t in p1["t"]]}\n{p1["r"]}'
                            )

                        if p2 is None:
                            row.append("-")
                        else:
                            row.append(
                                f'{self.data.subjects_info[p2["s"]].name}\n{[self.data.teachers_mapping[t] for t in p2["t"]]}\n{p2["r"]}'
                            )

                    writer.writerow(row)

    # def get_schedule_by_days(self):
    #     return [self.get_day_schedule(d) for d in self.data.days]

    # def get_day_schedule(self, d: int):
    #     return [self.get_class_schedule(c, d) for c in self.data.classes]

    # def get_class_schedule(self, c: int, d: int):
    #     return [self.get_period_info(c, d, p) for p in self.data.periods]

    def get_period_info(self, c: int, d: int, p: int):
        s = next(
            (
                x["s"]
                for x in self.variable_groups["schedule_subjects"]
                if x["value"]
                if x["d"] == d
                if x["p"] == p
                if c in self.data.subjects_info[x["s"]].classes
            ),
            None,
        )
        if s is None:
            return None

        t = self.get_teachers(d, p, s)
        r = self.get_room(d, p, s)

        return {"s": s, "t": t, "r": r}

    def get_teachers(self, d: int, p: int, s: int):
        teachers = [
            x["t"]
            for x in self.variable_groups["schedule_teachers"]
            if x["value"]
            if x["d"] == d
            if x["p"] == p
            if x["s"] == s
        ]
        return teachers

    def get_room(self, d: int, p: int, s: int):
        room = next(
            (
                x["r"]
                for x in self.variable_groups["schedule_rooms"]
                if x["value"]
                if x["d"] == d
                if x["p"] == p
                if x["s"] == s
            ),
            None,
        )
        return room


if __name__ == "__main__":
    i = 1
    while True:
        try:
            with open(f"generated/variable_values{i}.json", encoding="utf-8") as f:
                variables = json.load(f)

            with open("input/real_info.json", encoding="utf-8") as f:
                data = ScheduleData(json.load(f))

            saver = SaveSchedule(
                data, variables["variable_groups"], variables["single_variables"]
            )
            saver.save_schedule(f"generated/schedule{i}.csv")
            i += 1
        except OSError:
            break
