from dataclasses import dataclass
from itertools import product
from ortools.sat.python import cp_model


from info import DAYS, PERIODS, CLASSES, TEACHERS, ROOMS, SUBJECTS, subjects_info

teachers = range(TEACHERS)
subjects = range(SUBJECTS)
classes = range(CLASSES)
days = range(DAYS)
periods = range(PERIODS)
rooms = range(ROOMS)

model = cp_model.CpModel()

schedule_subjects: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
schedule_teachers: dict[tuple[int, int, int, int], cp_model.IntVar] = {}

for c, d, p, s in product(classes, days, periods, subjects):
    schedule_subjects[c, d, p, s] = model.new_bool_var(f"{c},{d},{p},s{s}")

for c, d, p, t in product(classes, days, periods, teachers):
    schedule_teachers[c, d, p, t] = model.new_bool_var(f"{c},{d},{p},t{t}")

# at most one subject per period
for c, d, p in product(classes, days, periods):
    subjects_same_period = (schedule_subjects[c, d, p, s] for s in subjects)
    model.add_at_most_one(subjects_same_period)

# each subject appears n times
for c, s in product(classes, subjects):
    periods_same_subject = (
        schedule_subjects[c, d, p, s] for d in days for p in periods
    )
    if c in subjects_info[s].classes:
        model.add(sum(periods_same_subject) == subjects_info[s].periods_per_week)
    else:
        model.add(sum(periods_same_subject) == 0)


# no same subjects on the same day
for c, d, s in product(classes, days, subjects):
    periods_same_day_subject = (schedule_subjects[c, d, p, s] for p in periods)
    model.add_at_most_one(periods_same_day_subject)

# assign teachers
for c, d, p, s in product(classes, days, periods, subjects):
    for t in subjects_info[s].teachers:
        model.add(schedule_teachers[c, d, p, t] == 1).only_enforce_if(
            schedule_subjects[c, d, p, s]
        )
        model.add(schedule_teachers[c, d, p, t] == 0).only_enforce_if(
            schedule_subjects[c, d, p, s].negated()
        )


# no same teacher on the same period
for d, p, t in product(days, periods, teachers):
    teachers_same_period = (schedule_teachers[c, d, p, t] for c in classes)
    model.add_at_most_one(teachers_same_period)


solver = cp_model.CpSolver()
status = solver.solve(model)

if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
    for c in classes:
        print(f"Class {c + 1} Schedule:")
        for d in days:
            print(f"  Day {d + 1}: ", end="")
            for p in periods:
                for s in subjects:
                    subject = solver.value(schedule_subjects[c, d, p, s])
                    if subject:
                        assigned_teachers: list[int] = []
                        for t in teachers:
                            teacher = solver.value(schedule_teachers[c, d, p, t])
                            if teacher:
                                assigned_teachers.append(t)
                        print(
                            f"{subjects_info[s].name}:{assigned_teachers}".ljust(12),
                            end="",
                        )
                        break
                else:
                    print("".ljust(12), end="")
            print()
else:
    print("No solution found.")
