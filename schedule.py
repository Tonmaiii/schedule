import asyncio
import json
import time
from asyncio.subprocess import Process
from tkinter import E
from typing import Any, Callable

import minizinc
import psutil

from data import ScheduleData
from data_minizinc import minizinc_data
from utils import create_file


def kill_process_group(proc: Process):
    try:
        parent = psutil.Process(proc.pid)
        children = parent.children(recursive=True)  # Get all child processes
        for child in children:
            print(f"Killing child process {child.pid}")
            child.kill()  # Kill child processes
        print(f"Killing parent process {proc.pid}")
        parent.kill()  # Kill parent process
    except psutil.NoSuchProcess:
        print(f"Process {proc.pid} already terminated.")


# Keep a reference to the original terminate method
original_terminate = Process.terminate


def patched_terminate(self: Process):
    """Patched terminate method to properly kill subprocesses."""
    if self.returncode is None:  # Only terminate if still running
        print(f"Terminating process {self.pid} and its subprocesses...")
        kill_process_tree(self.pid)  # Kill process tree
        original_terminate(self)  # Call original terminate


# Monkey patch the method
Process.terminate = patched_terminate


def kill_process_tree(pid: int):
    """Kill a process and all of its children."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)  # Get all child processes
        for child in children:
            child.terminate()  # Terminate children first
        parent.terminate()  # Terminate parent process
    except psutil.NoSuchProcess:
        pass  # Process already gone


class Schedule:
    def __init__(self, schedule_data: ScheduleData):
        self.schedule_data = schedule_data
        self.data = minizinc_data(schedule_data)

        with create_file("generated/minizinc_data.json") as f:
            json.dump(self.data, f)

        self.solver = minizinc.Solver.lookup("cp-sat")
        self.model = minizinc.Model("model.mzn")
        self.instance = minizinc.Instance(self.solver, self.model)

        self.assign_data()
        self.task: asyncio.Task[None] | None = None

    def assign_data(self):
        for key, value in self.data.items():
            self.instance[key] = value

    def solve(self, callback: Callable[[Any], Any] | None = None):
        asyncio.run(self.iterate_solutions(callback))

    async def solve_async(self, callback: Callable[[Any], Any] | None = None):
        self.task = asyncio.create_task(self.iterate_solutions(callback))

    async def iterate_solutions(self, callback: Callable[[Any], Any] | None = None):
        print("Iterating solutions")
        try:
            async for result in self.instance.solutions(
                processes=8, intermediate_solutions=True
            ):
                if result.solution is not None:
                    self.save_variables(result.solution.__dict__)
                    if callback is not None:
                        callback(self.solution_json(result.solution.__dict__))
                print(result.statistics)
                print(result.status)
            if callback is not None:
                callback(None)
        except Exception as e:
            print(e)
            if callback is not None:
                callback(None)
        print("Finished iterating solutions")

    async def cancel(self):
        if self.task is not None:
            self.task.cancel()
            try:
                await self.task  # Ensure cancellation is handled
            except asyncio.CancelledError:
                print("Solver was cancelled.")

    def save_variables(self, obj: dict[str, Any]):
        with create_file("generated/variable_values.json") as f:
            json.dump({"input": self.schedule_data.to_json_object(), "output": obj}, f)
        print("saved variables")

    def solution_json(self, obj: dict[str, Any]):
        return json.dumps({"input": self.schedule_data.to_json_object(), "output": obj})
