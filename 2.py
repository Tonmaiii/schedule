from ortools.sat.python import cp_model
from itertools import product

# each period appears twice

NUM_PERIODS = 4
NUM_DAYS = 5
NUM_CLASSES = 10
NUM_SUBJECTS = 10

PERIODS = range(NUM_PERIODS)
DAYS = range(NUM_DAYS)
CLASSES = range(NUM_CLASSES)
SUBJECTS = range(NUM_SUBJECTS)

model = cp_model.CpModel()

schedule: dict[tuple[int, int, int, int], cp_model.IntVar] = {}

for c, d, p, s in product(CLASSES, DAYS, PERIODS, SUBJECTS):
    schedule[c, d, p, s] = model.new_bool_var(f"{c},{d},{p},{s}")

# at most one subject per period
for c, d, p in product(CLASSES, DAYS, PERIODS):
    subjects = (schedule[c, d, p, s] for s in SUBJECTS)
    model.add_at_most_one(subjects)

# each subject appears twice
for c in CLASSES:
    for s in SUBJECTS:
        periods = (schedule[c, d, p, s] for d in DAYS for p in PERIODS)
        model.add(sum(periods) == 2)

# no two subjects on the same day
for c, d, s in product(CLASSES, DAYS, SUBJECTS):
    periods = (schedule[c, d, p, s] for p in PERIODS)
    model.add_at_most_one(periods)

# no same subject on the same period
for d, p, s in product(DAYS, PERIODS, SUBJECTS):
    periods = (schedule[c, d, p, s] for c in CLASSES)
    model.add_at_most_one(periods)

solver = cp_model.CpSolver()
status = solver.solve(model)

if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
    for c in CLASSES:
        print(f"Class {c + 1} Schedule:")
        for d in DAYS:
            print(f"  Day {d + 1}: ", end="")
            for p in PERIODS:
                for s in SUBJECTS:
                    subject = solver.value(schedule[c, d, p, s])
                    if subject:
                        print(f"{s} ", end="")
                        break
                else:
                    print("  ", end="")
            print()
else:
    print("No solution found.")
