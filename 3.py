from dataclasses import dataclass
from itertools import product
from ortools.sat.python import cp_model


# which teachers teach which classes
# subjects_teachers = [
#     [0, 1, 2],
#     [0, 1],
#     [3, 4, 5, 6],
#     [3, 4, 5],
#     [7, 8],
#     [9, 10],
#     [11, 12, 13],
#     [11, 12, 13],
#     [14],
#     [15, 16],
#     [17, 18, 19],
# ]
subjects_teachers = [
    [0, 1],
    [2],
    [3],
    [4],
    [7, 8],
    [9, 10],
    [11],
    [11],
    [14],
    [15, 16],
    [17, 18],
]


# each class contains how many periods of each subject
classes_subjects = [
    [2, 2, 3, 2, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
]

NUM_TEACHERS = 20
NUM_SUBJECTS = len(subjects_teachers)
NUM_CLASSES = len(classes_subjects)
NUM_DAYS = 5
NUM_PERIODS = 5


teachers = range(NUM_TEACHERS)
subjects = range(NUM_SUBJECTS)
classes = range(NUM_CLASSES)
days = range(NUM_DAYS)
periods = range(NUM_PERIODS)

model = cp_model.CpModel()

schedule_subjects: dict[tuple[int, int, int, int], cp_model.IntVar] = {}
schedule_teachers: dict[tuple[int, int, int, int], cp_model.IntVar] = {}

for c, d, p, s in product(classes, days, periods, subjects):
    schedule_subjects[c, d, p, s] = model.new_bool_var(f"{c},{d},{p},s{s}")


for c, d, p, t in product(classes, days, periods, teachers):
    schedule_teachers[c, d, p, t] = model.new_bool_var(f"{c},{d},{p},t{t}")

# at most one subject per period
for c, d, p in product(classes, days, periods):
    teachers_same_period = (schedule_subjects[c, d, p, s] for s in subjects)
    model.add_at_most_one(teachers_same_period)

# each subject appears n times
for c, s in product(classes, subjects):
    periods_same_subject = (
        schedule_subjects[c, d, p, s] for d in days for p in periods
    )
    model.add(sum(periods_same_subject) == classes_subjects[c][s])

# no same subjects on the same day
for c, d, s in product(classes, days, subjects):
    periods_same_day_subject = (schedule_subjects[c, d, p, s] for p in periods)
    model.add_at_most_one(periods_same_day_subject)

# one teacher per period
for c, d, p in product(classes, days, periods):
    for s in subjects:
        available_teachers = [
            schedule_teachers[c, d, p, t] for t in subjects_teachers[s]
        ]
        model.add(  # cant use `add_exactly_one` with `only_enforce_if` for some reason
            sum(available_teachers) == 1
        ).only_enforce_if(schedule_subjects[c, d, p, s])
    teachers_same_period = (schedule_teachers[c, d, p, t] for t in teachers)
    model.add_exactly_one(teachers_same_period)

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
                        for t in teachers:
                            teacher = solver.value(schedule_teachers[c, d, p, t])
                            if teacher:
                                print(f"{s}:{t}".ljust(6), end="")
                                break
                        else:
                            print(f"{s}:N ".ljust(6), end="")
                        break
                else:
                    print("      ", end="")
            print()
else:
    print("No solution found.")
