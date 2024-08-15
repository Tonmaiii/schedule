from schedule import Schedule

if __name__ == "__main__":
    schedule = Schedule(optimize_distance=False, use_alternating_weeks=True)
    schedule.solve_and_print()
