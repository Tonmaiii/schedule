from typing import TYPE_CHECKING
from ortools.sat.python import cp_model


if TYPE_CHECKING:
    from schedule import Schedule


class PrintSolutions(cp_model.CpSolverSolutionCallback):
    def __init__(self, schedule: "Schedule"):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.schedule = schedule

    def on_solution_callback(self):
        for c in self.schedule.data.classes:
            print(f"Class {c} Schedule:")
            for d in self.schedule.data.days:
                print(f"  Day {d}: ", end="")
                for p in self.schedule.data.periods:
                    for s in self.schedule.data.subjects:
                        if c not in self.schedule.data.subjects_info[s].classes:
                            continue
                        subject = self.value(self.schedule.schedule_subjects[d, p, s])
                        assert subject == self.value(
                            self.schedule.schedule_subjects_by_classes[c, d, p, s]
                        )
                        if not subject:
                            continue
                        subject_info = self.schedule.data.subjects_info[s]

                        room = None
                        for r in subject_info.available_rooms:
                            room_value = self.value(
                                self.schedule.schedule_rooms[d, p, s, r]
                            )
                            assert room_value == self.value(
                                self.schedule.schedule_rooms_by_classes[c, d, p, r]
                            )

                            if not room_value:
                                continue
                            room = r
                            break

                        teachers: list[int] = []
                        for t in subject_info.teachers:
                            teacher_value = self.value(
                                self.schedule.schedule_teachers[d, p, s, t]
                            )
                            if not teacher_value:
                                continue
                            teachers.append(t)

                        print(
                            f"{subject_info.name}:{teachers}:{room}".ljust(18),
                            end="",
                        )
                        break
                    else:
                        print("".ljust(18), end="")

                    if p == self.schedule.data.num_periods - 1:
                        break
                    distance = self.value(
                        self.schedule.schedule_room_distances[d, p, c]
                    )
                    print(f"{distance}".ljust(4), end="")
                print()
        print(f"max distance per day: {self.value(self.schedule.max_distance)}")
        print(f"sum distance: {self.value(self.schedule.sum_distance)}")


# def stop_after_n_solutions_sample_sat():
#     """Showcases calling the solver to search for small number of solutions."""
#     # Creates the model.
#     model = cp_model.CpModel()
#     # Creates the variables.
#     num_vals = 3
#     x = model.new_int_var(0, num_vals - 1, "x")
#     y = model.new_int_var(0, num_vals - 1, "y")
#     z = model.new_int_var(0, num_vals - 1, "z")

#     # Create a solver and solve.
#     solver = cp_model.CpSolver()
#     solution_printer = VarArraySolutionPrinterWithLimit([x, y, z], 5)
#     # Enumerate all solutions.
#     solver.parameters.enumerate_all_solutions = True
#     # Solve.
#     status = solver.solve(model, solution_printer)
#     print(f"Status = {solver.status_name(status)}")
#     print(f"Number of solutions found: {solution_printer.solution_count}")
#     assert solution_printer.solution_count == 5


# stop_after_n_solutions_sample_sat()
