import json

from data import ScheduleData
from schedule import Schedule

if __name__ == "__main__":

    with open("input/data_50.json", encoding="utf-8") as f:
        data = json.load(f)

    schedule = Schedule(ScheduleData(data))
    schedule.solve()
