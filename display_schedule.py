import csv
import json
from dataclasses import dataclass
from typing import Any, Counter

from data import ScheduleData
from utils import create_file


@dataclass
class SaveSchedule:
    data: ScheduleData
    variables: dict[str, Any]

    def save_teacher_assignments(self, path: str):
        with create_file(path) as f:
            obj = {
                q.name: Counter(
                    t for s in q.subjects for t in self.get_teachers_for_subject(s)
                )
                for q in self.data.courses_data
            }
            json.dump(obj, f, ensure_ascii=False)

    def get_teachers_for_subject(self, s: int):
        return [t for t in self.data.teachers if variables["teacher_assignments"][s][t]]

    def save_schedule(self, path: str):
        with create_file(path) as f:
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
                    row: list[Any] = [d + 1, self.data.classes_data[c].name]
                    for p in self.data.periods:
                        if self.data.config.use_alternating_weeks:
                            p1 = self.get_period_info(c, d, p)
                            p2 = self.get_period_info(c, d + self.data.num_days // 2, p)

                            row.append(self.period_text(p1))
                            row.append(self.period_text(p2))

                            if (
                                self.data.config.optimize_distance
                                and p != self.data.num_periods - 1
                            ):
                                row.append(self.get_distance(c, d, p))
                                row.append(
                                    self.get_distance(c, d + self.data.num_days // 2, p)
                                )
                        else:
                            p1 = self.get_period_info(c, d, p)
                            row.append(self.period_text(p1))
                            if (
                                self.data.config.optimize_distance
                                and p != self.data.num_periods - 1
                            ):
                                row.append(self.get_distance(c, d, p))

                    writer.writerow(row)

    def period_text(
        self,
        p: dict[str, Any],
    ):
        if p["s"] is None:
            return "-"
        if self.data.config.schedule_rooms and p["r"] is not None:
            return f"""{self.data.subjects_data[p["s"]].name}
{", ".join(self.data.teachers_data[t].name for t in p["t"])}
{", ".join(self.data.rooms_data[r].name for r in p["r"])}"""

        return f'{self.data.subjects_data[p["s"]].name}\n{", ".join(self.data.teachers_data[t].name for t in p["t"])}'

    def get_period_info(self, c: int, d: int, p: int):
        s = next(
            (
                s
                for s in self.data.subjects
                if c in self.data.subjects_data[s].classes
                if self.variables["schedule_subjects"][d][p][s]
            ),
            None,
        )
        if s is None:
            return {"s": None, "t": None, "r": None}

        t = self.get_teachers(s)
        r = self.get_rooms(s)
        return {"s": s, "t": t, "r": r}

    def get_teachers(self, s: int):
        teachers = [
            t for t in self.data.teachers if self.variables["teacher_assignments"][s][t]
        ]
        return teachers

    def get_rooms(self, s: int):
        rooms = [r for r in self.data.rooms if self.variables["room_assignments"][s][r]]
        return rooms

    def get_distance(self, c: int, d: int, p: int):
        distance = self.variables["distances"][c][d][p]
        return distance


if __name__ == "__main__":
    with open("generated/variable_values.json", encoding="utf-8") as f:
        obj = json.load(f)
    data = ScheduleData(obj["input"])
    variables = obj["output"]

    saver = SaveSchedule(data, variables)
    saver.save_schedule("generated/schedule.csv")
    saver.save_teacher_assignments("generated/teachers.json")
