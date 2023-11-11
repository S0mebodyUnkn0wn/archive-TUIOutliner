import datetime
import pickle
from dataclasses import dataclass
from typing import overload

from OutlinerApp.Backend.configs import session_config
from OutlinerApp.Backend.events import Event
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

    @property
    def icon(self):
        return session_config.Icons.generic_event_icon

    @staticmethod
    def from_event(event: Event):
        return TimetableEvent(date=event.date, name=event.text, start_time=event.time, event=event)

    @staticmethod
    def from_task_with_deadline(task: TaskNode):
        if task.deadline is None:
            raise AttributeError("Deadline field cannot be None when adding a task to a timetable")
        return TimetableTask(date=task.deadline, name=task.text, task=task)

    @property
    def is_momentary(self) -> bool:
        return self.start_time == self.end_time

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
        if isinstance(other,TimetableTask):
            return self.task == other.task
        return same


@dataclass
class TimetableEvent(TimetableItem):
    event: Event = None
    item_type: str = "EVENT"

    @property
    def icon(self):
        return self.event.icon

    def __eq__(self, other):
        same = super().__eq__(other)
        if isinstance(other, TimetableEvent):
            return self.event == other.event
        return same


class Timetable:
    daytables_by_date: dict[datetime.date, list[TimetableItem]]

    def __init__(self):
        self.daytables_by_date = {}

    def find_item(self, serachitem: TaskNode):
        if isinstance(serachitem, TaskNode):
            if serachitem.deadline not in self.daytables_by_date.keys():
                return None
            day_timetable = self.daytables_by_date[serachitem.deadline]

            for item in day_timetable:
                if isinstance(item,TimetableTask) and item.task == serachitem:
                    return item

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

    @overload
    def remove_item(self, task: "TaskNode"):
        ...

    def remove_item(self, *args):
        date: datetime.date
        index: int
        if len(args) == 1 and isinstance(args[0], TimetableItem):
            task_to_remove: TimetableItem = args[0]
            date = task_to_remove.date
            if date in self.daytables_by_date.keys():
                items: list[TimetableItem] = self.daytables_by_date[date]
                items.remove(task_to_remove)
                return

        if len(args) == 2 and isinstance(args[0], datetime.date) and isinstance(args[1], int):
            date = args[0]
            index = args[1]
            if date in self.daytables_by_date.keys():
                items: list[TimetableItem] = self.daytables_by_date[date]
                if 0 <= index < len(items):
                    items.pop(index)

    def load_pickle(self, file):
        new_timetable = pickle.load(file)
        self.daytables_by_date = new_timetable
