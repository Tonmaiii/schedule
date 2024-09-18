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
                if not self.data.config.use_alternating_weeks:
                    if self.data.config.optimize_distance:
                        header.append(f"{p+1}")
                        header.append(f"d{p+1}")
                    else:
                        header.append(f"{p+1}")
                else:
                    if self.data.config.optimize_distance:
                        header.append(f"{p+1}A")
                        header.append(f"{p+1}B")
                        header.append(f"d{p+1}A")
                        header.append(f"d{p+1}B")
                    else:
                        header.append(f"{p+1}A")
                        header.append(f"{p+1}B")

            writer.writerow(header)

            for d in range(
                self.data.num_days // 2
                if self.data.config.use_alternating_weeks
                else self.data.num_days
            ):
                for c in self.data.classes:
                    row: list[Any] = [d + 1, c + 1]
                    for p in self.data.periods:
                        if self.data.config.use_alternating_weeks:
                            p1 = self.get_period_info(c, d, p)
                            p2 = self.get_period_info(c, d + self.data.num_days // 2, p)

                            row.append(self.period_text(p1))
                            row.append(self.period_text(p2))

                            if self.data.config.optimize_distance:
                                row.append(self.get_distance(c, d, p))
                                row.append(
                                    self.get_distance(c, d + self.data.num_days // 2, p)
                                )
                        else:
                            p1 = self.get_period_info(c, d, p)
                            row.append(self.period_text(p1))
                            if self.data.config.optimize_distance:
                                row.append(self.get_distance(c, d, p))

                    writer.writerow(row)

    def period_text(
        self,
        p: dict[str, Any] | None,
    ):
        if p is None:
            return "-"
        return f'{self.data.subjects_info[p["s"]].name}\n{", ".join(self.data.teachers_mapping[t] if self.data.teachers_mapping else t for t in p["t"])}\n{p["r"]}'

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

    def get_distance(self, c: int, d: int, p: int):
        distance = next(
            (
                x["value"]
                for x in self.variable_groups["schedule_room_distances"]
                if x["d"] == d
                if x["p"] == p
                if x["c"] == c
            ),
            0,
        )
        return distance


if __name__ == "__main__":
    with open("generated/variable_values.json", encoding="utf-8") as f:
        variables = json.load(f)

    with open("input/real_info.json", encoding="utf-8") as f:
        data = ScheduleData(json.load(f))

    saver = SaveSchedule(
        data, variables["variable_groups"], variables["single_variables"]
    )
    saver.save_schedule("generated/schedule.csv")
