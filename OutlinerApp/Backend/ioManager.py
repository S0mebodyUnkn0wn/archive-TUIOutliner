#!/usr/bin/python3
import datetime
import pickle
from typing import overload

from ..Backend.configs import session_config
from ..Backend.tasks import TaskNode
from ..Backend.timetables import Timetable, TimetableItem

_root_task: TaskNode | None = None
_timetable: Timetable | None = None


def get_root_task():
    global _root_task
    if _root_task is None:
        load_tasks()
    return _root_task


def get_timetable():
    global _timetable
    if _timetable is None:
        load_events()
        if _timetable is None:
            raise RuntimeError()
    return _timetable


def add_subtask(subtask: TaskNode, root = _root_task):
    global _root_task
    global _timetable
    if root is None:
        load_tasks()
        root = _root_task
    root.add_subtask(subtask)
    if subtask.deadline is not None:
        _timetable.add_item(TimetableItem.from_task_with_deadline(subtask))
        dump_timetable()
    dump_tasks()


def mark_done(task: TaskNode):
    tt = _timetable.find_item(task)
    if tt is not None:
        tt.task.toggle_done()
    if tt.__repr__() != task.__repr__():
        task.toggle_done()
    dump_timetable()
    dump_tasks()


def edit_event(event: TimetableItem, new_event: TimetableItem):
    if event.date!= new_event.date:
        _timetable.move_item(event,new_event.date)
    event.name = new_event.name
    event.start_time = new_event.start_time
    dump_timetable()
    return event


def edit_task(task: TaskNode, new_text=None, new_deadline=None):
    if isinstance(new_text, str):
        tt = _timetable.find_item(task)
        task.text = new_text
        if tt is not None:
            tt.task = task
            tt.name = tt.task.text
    if isinstance(new_deadline,datetime.date) or new_deadline=="":
        if new_deadline == "":
            new_deadline = None
        if task.deadline is not None:
            _timetable.remove_item(TimetableItem.from_task_with_deadline(task))
        task.deadline = new_deadline
        if new_deadline is not None:
            _timetable.add_item(TimetableItem.from_task_with_deadline(task))
    dump_timetable()
    dump_tasks()
    return task


def remove_task(task: TaskNode):
    global _root_task
    global _timetable
    task.remove()
    try:
        if task.deadline is not None:
            _timetable.remove_item(TimetableItem.from_task_with_deadline(task))
            dump_timetable()
    except ValueError:
        pass
    dump_tasks()


def add_to_timetable(item: TimetableItem):
    global _root_task
    global _timetable
    _timetable.add_item(item)
    dump_timetable()

@overload
def remove_from_timetable(item: TimetableItem):
    ...

@overload
def remove_from_timetable(date: datetime.date, num: int):
    ...

def remove_from_timetable(*args):
    global _root_task
    global _timetable
    if len(args) == 2 and isinstance(args[0], datetime.date) and isinstance(args[1], int):
        _timetable.remove_item(args[0], args[1])
    if len(args) == 1 and isinstance(args[0], TimetableItem):
        _timetable.remove_item(args[0])
    dump_timetable()


def load_events():
    global _root_task
    global _timetable
    if session_config.IOConfig.event_file.is_file():
        with open(session_config.IOConfig.event_file, "rb") as file:
            try:
                _timetable = pickle.load(file)
            except EOFError:
                _timetable = Timetable()


def dump_timetable():
    global _root_task
    global _timetable
    with open(session_config.IOConfig.event_file, "wb") as file:
        pickle.dump(_timetable, file)


def load_tasks():
    global _root_task
    global _timetable
    with open(session_config.IOConfig.tasks_file, "rb") as file:
        try:
            _root_task = pickle.load(file)
        except EOFError:
            _root_task = TaskNode()
    _root_task.sort_children()


def dump_tasks():
    global _root_task
    global _timetable
    with open(session_config.IOConfig.tasks_file, "wb") as file:
        pickle.dump(_root_task, file)

