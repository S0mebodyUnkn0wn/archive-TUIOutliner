#!/usr/bin/python3
import datetime
import pickle

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


def edit_task(task: TaskNode, new_text=None, new_deadline=None):
    if isinstance(new_text, str):
        tt = _timetable.find_item(task)
        task.text = new_text
        if tt is not None:
            tt.task = task
            tt.name = tt.task.text
    if isinstance(new_deadline,datetime.date):
        if task.deadline is not None:
            _timetable.remove_item(TimetableItem.from_task_with_deadline(task))
        task.deadline = new_deadline
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


def remove_from_timetable(date: datetime.date, num: int):
    global _root_task
    global _timetable
    _timetable.remove_item(date, num)
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

