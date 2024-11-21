from typing import Any, TypeVar

from data import CourseData, ScheduleData

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
        "num_courses": data.num_courses,
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
                    "course": s.course,
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
        **pivot_to_lists(
            [
                {
                    "available_periods": [
                        [[d, p] in r.available_periods for p in data.periods]
                        for d in data.days
                    ],
                }
                for r in data.rooms_data
            ],
            "rooms__",
        ),
        **pivot_to_lists(
            [course(q, data) for q in data.courses_data],
            "courses__",
        ),
    }


def course(q: CourseData, data: ScheduleData) -> dict[str, Any]:
    at_least = [0] * data.num_teachers
    at_most = [0] * data.num_teachers
    if q.teacher_distribution is not None:
        for td in q.teacher_distribution:
            at_least[td.teacher] = td.at_least
            at_most[td.teacher] = td.at_most
    return {
        "at_least": at_least,
        "at_most": at_most,
        "subjects": json_set(q.subjects),
        "do_distribute_teachers": q.do_distribute_teachers,
    }


def pivot_to_lists(data: list[dict[str, T]], prefix: str = "") -> dict[str, list[T]]:
    if not data:
        return {}

    result: dict[str, list[T]] = {f"{prefix}{key}": [] for key in data[0]}

    for entry in data:
        for key, value in entry.items():
            result[f"{prefix}{key}"].append(value)

    return result


def json_set(lst: list[T] | None = None):
    return {"set": lst if lst else []}
