from dataclasses import dataclass
from itertools import product
from ortools.sat.python import cp_model


# which teachers teach which classes
subjects_teachers = [
    [0, 1, 2],
    [0, 1],
    [3, 4, 5, 6],
    [3, 4, 5],
    [7, 8],
    [9, 10],
    [11, 12, 13],
    [11, 12, 13],
    [14],
    [15, 16],
    [17, 18, 19],
]


# each class contains how many periods of each subject
classes_subjects = [
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
    [2, 2, 3, 2, 1, 1, 2, 2, 1, 3, 2],
]

NUM_TEACHERS = 20
NUM_subjects = len(subjects_teachers)
NUM_CLASSES = len(classes_subjects)
NUM_days = 5
NUM_periods = 5


teachers = range(NUM_TEACHERS)
subjects = range(NUM_subjects)
classes = range(NUM_CLASSES)
days = range(NUM_days)
periods = range(NUM_periods)

model = cp_model.CpModel()
a = 123

schedule: dict[tuple[int, int, int, int, int], cp_model.IntVar] = {}

for c, d, p, s, t in product(classes, days, periods, subjects, teachers):
    schedule[c, d, p, s, t] = model.new_bool_var(f"{c},{d},{p},{s},{t}")

# at most one subject per period
for c, d, p in product(classes, days, periods):
    subjects = (schedule[c, d, p, s] for s in subjects)
    model.add_at_most_one(subjects)

# each subject appears twice
for c in classes:
    for s in subjects:
        periods = (schedule[c, d, p, s] for d in days for p in periods)
        model.add(sum(periods) == 2)

# no two subjects on the same day
for c, d, s in product(classes, days, subjects):
    periods = (schedule[c, d, p, s] for p in periods)
    model.add_at_most_one(periods)

# no same subject on the same period
for d, p, s in product(days, periods, subjects):
    periods = (schedule[c, d, p, s] for c in classes)
    model.add_at_most_one(periods)

solver = cp_model.CpSolver()
status = solver.solve(model)
