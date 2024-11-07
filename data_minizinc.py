import json
from typing import Any, TypeVar

from data import ScheduleData

T = TypeVar("T")


def minizinc_data(data: ScheduleData) -> dict[str, Any]:
    return {
        "do_schedule_rooms": data.config.schedule_rooms,
        "optimize_distances": data.config.optimize_distance,
        "use_alternating_weeks": data.config.use_alternating_weeks,
        "num_days": data.num_days,
        "num_periods": data.num_periods,
        "num_subjects": data.num_subjects,
        "num_teachers": data.num_teachers,
        "num_rooms": data.num_rooms,
        "num_classes": data.num_classes,
        "room_distances": data.room_distances,
        **pivot_to_lists(
            [
                {
                    "classes": json_set(s.classes),
                    "periods_per_week": s.periods_per_week,
                    "teachers_per_period": s.teachers_per_period,
                    "teachers": json_set(s.teachers),
                    "rooms_per_period": s.rooms_per_period,
                    "rooms": json_set(s.available_rooms),
                    "available_periods": [
                        [[d, p] in s.available_periods for p in data.periods]
                        for d in data.days
                    ],
                }
                for s in data.subjects_data
            ],
            "subjects__",
        ),
        **pivot_to_lists(
            [
                {
                    "available_periods": [
                        [[d, p] in t.available_periods for p in data.periods]
                        for d in data.days
                    ],
                }
                for t in data.teachers_data
            ],
            "teachers__",
        ),
    }


def pivot_to_lists(data: list[dict[str, T]], prefix: str = "") -> dict[str, list[T]]:
    if not data:
        return {}

    result: dict[str, list[T]] = {f"{prefix}{key}": [] for key in data[0]}

    for entry in data:
        for key, value in entry.items():
            result[f"{prefix}{key}"].append(value)

    return result


def json_set(lst: list[T]):
    return {"set": lst}
