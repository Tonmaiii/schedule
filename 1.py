from ortools.sat.python import cp_model

num_classes = 4
num_days = 5
num_periods = 4
num_subjects = 20

model = cp_model.CpModel()

schedule = {}
for c in range(num_classes):
    for d in range(num_days):
        for p in range(num_periods):
            schedule[(c, d, p)] = model.NewIntVar(
                0, num_subjects - 1, f"schedule_c{c}_d{d}_p{p}"
            )

for c in range(num_classes):
    weekly_subjects = []
    for d in range(num_days):
        for p in range(num_periods):
            weekly_subjects.append(schedule[(c, d, p)])
    model.AddAllDifferent(weekly_subjects)

for p in range(num_periods):
    same_period = []
    for d in range(num_days):
        for c in range(num_classes):
            same_period.append(schedule[(c, d, p)])
    model.AddAllDifferent(same_period)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
    for c in range(num_classes):
        print(f"Class {c + 1} Schedule:")
        for d in range(num_days):
            print(f"  Day {d + 1}: ", end="")
            for p in range(num_periods):
                subject = solver.Value(schedule[(c, d, p)])
                print(f"{subject} ", end="")
            print()
else:
    print("No solution found.")
