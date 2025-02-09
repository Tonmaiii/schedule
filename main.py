import json
from sys import argv

from data import ScheduleData
from schedule import Schedule

if __name__ == "__main__":
    with open(argv[1], encoding="utf-8") as f:
        data = json.load(f)
    schedule = Schedule(ScheduleData(data))
    schedule.solve()
