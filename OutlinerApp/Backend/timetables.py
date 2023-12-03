import datetime
import pickle
from dataclasses import dataclass
from typing import overload

from OutlinerApp.Backend.configs import session_config
from OutlinerApp.Backend.tasks import TaskNode


# TODO We're gonna need a task schedule overlay


@dataclass
class TimetableItem:
    date: datetime.date
    name: str

    TID: int = 0

    location: str | None = None
    description: str | None = None

    start_time: datetime.time = None
    end_time: datetime.time = None

    people: NotImplemented = None
    item_type: NotImplemented = None

    def __post_init__(self):
        self.TID = TimetableItem.TID
        TimetableItem.TID += 1
        if self.end_time is None:
            self.end_time = self.start_time

    @property
    def icon(self):
        return session_config.Icons.generic_event_icon

    @staticmethod
    def from_task_with_deadline(task: TaskNode):
        if task.deadline is None:
            raise AttributeError("Deadline field cannot be None when adding a task to a timetable")
        return TimetableTask(date=task.deadline, name=task.text, task=task)

    @property
    def is_momentary(self) -> bool:
        return self.start_time == self.end_time

    def __str__(self):
        return self.name
    # is_recurring: bool


@dataclass
class TimetableTask(TimetableItem):
    task: TaskNode = None
    item_type: str = "TASK"

    @property
    def icon(self):
        return self.task.icon

    def __eq__(self, other):
        same = super().__eq__(other)
        if isinstance(other, TimetableTask):
            return self.task == other.task
        return same


class Timetable:
    daytables_by_date: dict[datetime.date, list[TimetableItem]]

    def __init__(self):
        self.daytables_by_date = {}

    def move_item(self, item: TimetableItem, new_date: datetime.date):
        if self.remove_item(item) is None:
            return None
        item.date = new_date
        self.add_item(item)

    @overload
    def find_item(self, date: datetime.date, num: int):
        ...

    @overload
    def find_item(self, serachitem: TaskNode):
        ...

    def find_item(self, *args):
        if len(args)==1 and isinstance(args[0], TaskNode):
            searchitem = args[0]
            if searchitem.deadline not in self.daytables_by_date.keys():
                return None
            day_timetable = self.daytables_by_date[searchitem.deadline]

            for item in day_timetable:
                if isinstance(item, TimetableTask) and item.task == searchitem:
                    return item
        if len(args)==2 and isinstance(args[0], datetime.date) and isinstance(args[1], int):
            date = args[0]
            index = args[1]
            if date in self.daytables_by_date.keys():
                items: list[TimetableItem] = self.daytables_by_date[date]
                if 0 <= index < len(items):
                    return items[index]

        return None

    def add_item(self, new_item: TimetableItem, overwrite_existing: bool = False):
        if new_item.date in self.daytables_by_date.keys():
            day_timetable = self.daytables_by_date[new_item.date]

            # Always append tasks to the end of the day's events
            if isinstance(new_item, TimetableTask):
                day_timetable.append(new_item)
                return

            index = -1
            for item in day_timetable:
                index += 1
                if item.start_time is None:
                    day_timetable.insert(index, new_item)
                    break
                if item.end_time <= new_item.start_time:
                    continue
                elif item.start_time >= new_item.end_time:
                    day_timetable.insert(index, new_item)
                    break
                else:
                    raise RuntimeError
            else:
                day_timetable.append(new_item)
        else:
            day_timetable = [new_item]

            self.daytables_by_date[new_item.date] = day_timetable

    @overload
    def remove_item(self, timetable_item: TimetableItem):
        ...

    @overload
    def remove_item(self, date: datetime.date, index: int):
        ...

    def remove_item(self, *args):
        date: datetime.date
        index: int
        if len(args) == 1 and isinstance(args[0], TimetableItem):
            item_to_remove: TimetableItem = args[0]
            date = item_to_remove.date
            if date in self.daytables_by_date.keys():
                items: list[TimetableItem] = self.daytables_by_date[date]
                items.remove(item_to_remove)
                return item_to_remove

        if len(args) == 2 and isinstance(args[0], datetime.date) and isinstance(args[1], int):
            date = args[0]
            index = args[1]
            if date in self.daytables_by_date.keys():
                items: list[TimetableItem] = self.daytables_by_date[date]
                if 0 <= index < len(items):
                    return items.pop(index)

        return None

    def load_pickle(self, file):
        new_timetable = pickle.load(file)
        self.daytables_by_date = new_timetable
