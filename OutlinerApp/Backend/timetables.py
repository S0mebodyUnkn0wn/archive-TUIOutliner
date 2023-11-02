import datetime
import pickle
from dataclasses import dataclass
from typing import overload

from OutlinerApp.Backend.events import Event
from OutlinerApp.Backend.tasks import TaskNode


# TODO We're gonna need a task schedule overlay


@dataclass
class TimeTableItem:
    start_time: datetime.datetime
    end_time: datetime.datetime

    name: str
    location: str | None = None
    description: str | None = None

    people: NotImplemented = None
    item_type: NotImplemented = None

    @property
    def is_momentary(self) -> bool:
        return self.start_time == self.end_time

    # is_recurring: bool


@dataclass
class TimeTableRecurring(TimeTableItem):
    pass


@dataclass
class TimeTableTask(TimeTableItem):
    task: TaskNode = None

    def __post_init__(self):
        self.name = self.task.text


@dataclass
class TimeTableEvent(TimeTableItem):
    event: Event = None

    def __post_init__(self):
        self.name = self.event.text


class TimeTable:
    daytables_by_date: dict[datetime.date, list[TimeTableItem]]

    def __init__(self):
        self.daytables_by_date = {}

    def add_item(self, new_item: TimeTableItem, overwrite_existing: bool = False):
        if new_item.start_time.date() in self.daytables_by_date.keys():
            day_timetable = self.daytables_by_date[new_item.start_time.date()]

            index = -1
            for item in day_timetable:
                index += 1
                if item.end_time <= new_item.start_time:
                    continue
                elif item.start_time >= new_item.end_time:
                    day_timetable.insert(index, new_item)
                    break
                else:
                    raise RuntimeError
        else:
            day_timetable = [new_item]

            self.daytables_by_date[new_item.start_time.date()] = day_timetable

    @overload
    def remove_item(self, timetable_item: TimeTableItem):
        ...

    @overload
    def remove_item(self, date: datetime.date, index: int):
        ...

    def remove_item(self, *args):
        date: datetime.date
        index: int
        if len(args) == 1 and isinstance(args[0], TimeTableItem):
            item_to_remove: TimeTableItem = args[0]
            date = item_to_remove.start_time.date()
            if date in self.daytables_by_date.keys():
                items: list[TimeTableItem] = self.daytables_by_date[date]
                items.remove(item_to_remove)

        if len(args) == 2 and isinstance(args[0], datetime.date) and isinstance(args[1], int):
            date = args[0]
            index = args[1]
            if date in self.daytables_by_date.keys():
                items: list[TimeTableItem] = self.daytables_by_date[date]
                if 0 <= index < len(items):
                    items.pop(index)

    def load_pickle(self, file):
        new_timetable = pickle.load(file)
        self.daytables_by_date = new_timetable
        