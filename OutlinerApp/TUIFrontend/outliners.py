import calendar
import curses
import datetime
import pickle

from Backend import ioManager
from Backend.timetable import Timetable
from .widgets import Widget
from ..Backend import data
from ..Backend.configs import session_config
from ..Backend.events import EventCalendar, Event
from ..Backend.tasks import TaskNode


class Outliner(Widget):
    config = session_config.OutlinerConfig
    remove_mode = False

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0, input_manager=None):
        super().__init__(stdscr, x_offset, y_offset, input_manager)
        self.margins = self.config.margins
        self.header_margin = 2
        self.fixed_width = self.config.fixed_width
        self.fixed_length = self.config.fixed_length

    def remove_entry(self):
        pass

    def add_entry(self):
        pass

    def scroll(self, direction: (int, int)):
        pass

    def update(self):
        super().update()

    def render_header(self, color=None):
        if color is None:
            color = session_config.ColorsConfig.selected_pair if self.is_focused \
                else session_config.ColorsConfig.generic_text_pair
        if self.header is None:
            return
        self.stdscr.addnstr(self.top, self.left + self.header_margin,
                            f"{self.header}", self.width - self.header_margin * 2, curses.color_pair(color))


class TaskOutliner(Outliner):
    tasks: list[TaskNode]
    root_task: TaskNode
    line_count: int
    config = session_config.TaskOutlinerConfig
    ID = 0

    @staticmethod
    def reload_data():

        new_root_task = ioManager.load_tasks()

        TaskOutliner.root_task = new_root_task

        TaskOutliner.tasks = TaskOutliner.root_task.get_all_children()
        TaskOutliner.line_count = len(TaskOutliner.tasks)

    @staticmethod
    def toggle_hide_done():
        # TODO Questionable implementation
        if data.Importance.DONE in session_config.TaskConfig.exclude_tasks:
            session_config.TaskConfig.exclude_tasks.remove(data.Importance.DONE)
        else:
            session_config.TaskConfig.exclude_tasks.append(data.Importance.DONE)

    @staticmethod
    def _select_color(task):
        color = session_config.ColorsConfig.generic_text_pair
        if task.importance == data.Importance.DONE:
            color = session_config.ColorsConfig.done_pair
        elif data.Importance.DOING_C <= task.importance <= data.Importance.DOING_A:
            color = session_config.ColorsConfig.doing_pair
        elif data.Importance.WAITING_C <= task.importance <= data.Importance.WAITING_A:
            color = session_config.ColorsConfig.waiting_pair
        return color

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0):
        super().__init__(stdscr, x_offset, y_offset)
        self.config = session_config.TaskOutlinerConfig
        self.start_line = 0
        self.reload_data()

    @property
    def header(self):
        return f"TODO List"

    def update(self):
        super().update()
        self.reload_data()

    def scroll(self, direction: (int, int)):
        super().scroll(direction)
        lines = direction[0]
        if 0 <= self.start_line + lines < self.line_count:
            self.start_line += lines

    def add_entry(self):
        task_text = self.input_manager.recieve_text("Enter task: ")
        if len(task_text) == 0:
            return False

        deadline_str = self.input_manager.recieve_text("Enter task deadline (dd/mm/yyyy): ", split_mask="__/__/____")
        if len(deadline_str) == 10:
            deadline_str: str
            deadline_str = deadline_str.split("/")
            task_deadline = datetime.date(int(deadline_str[2]), int(deadline_str[1]), int(deadline_str[0]))
        else:
            task_deadline = None
        new_task = TaskNode(text=task_text, deadline=task_deadline)
        self.root_task.add_subtask(new_task)
        ioManager.dump_tasks(self.root_task)

    def remove_entry(self):
        TaskOutliner.remove_mode = True
        self.update()
        task_str = self.input_manager.recieve_text("Delete task number:")
        if len(task_str) != 0:
            task_num = int(task_str)
            if 1 <= task_num <= len(self.tasks):
                self.tasks[task_num - 1].remove()
                ioManager.dump_tasks(self.root_task)
        TaskOutliner.remove_mode = False

    def mark_done(self):
        self.modify_task(job="mark done")

    def modify_task(self, job: str):
        TaskOutliner.remove_mode = True
        self.update()
        prompt = job
        match job:
            case "mark done":
                prompt = "Mark as done task number:"

        task_str = self.input_manager.recieve_text(prompt)
        if len(task_str) != 0:
            task_num = int(task_str)
            if 1 <= task_num <= len(self.tasks):
                self.tasks[task_num - 1].mark_done()
                ioManager.dump_tasks(self.root_task)
        TaskOutliner.remove_mode = False

    def render(self):

        line = 0 - self.start_line
        for index in range(len(self.tasks)):
            task: TaskNode = self.tasks[index]

            if self.content_length >= line >= 0:

                output = f"{(str(self.tasks.index(task) + 1) + ' ') if TaskOutliner.remove_mode else ''}" \
                         f"{task.to_cli_format()}"
                right = self.content_left + self.content_width

                if task.deadline is not None:
                    color = session_config.ColorsConfig.deadline_pair if task.importance != data.Importance.DONE \
                        else session_config.ColorsConfig.done_pair
                    deadline = session_config.Icons.deadline_icon + datetime.date.strftime(task.deadline, "%Y/%m/%d")
                    deadline_start_x = self.content_left + self.content_width - len(deadline)
                    if deadline_start_x < curses.COLS:
                        self.stdscr.addnstr(self.content_top + line, deadline_start_x, deadline,
                                            self.width - deadline_start_x + self.content_left, curses.color_pair(color))
                    right = deadline_start_x

                if self.content_left + len(output) >= right:
                    output = output[0:right - self.content_left - 4]
                    output += "..."

                color = self._select_color(task)

                self.stdscr.addnstr(self.content_top + line, self.content_left, output,
                                    self.content_width, curses.color_pair(color))
            line += 1
        self.render_frame()
        self.render_header()


class CalendarOutliner(Outliner):
    timetable = Timetable()
    config = session_config.EventOutlinerConfig
    widget_title = "Events"
    show_tasks = True
    ID = 1

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0):
        super().__init__(stdscr, x_offset, y_offset)
        self.open_date = datetime.date.today()
        self.reload_data()

    @property
    def header(self):
        out = f"{calendar.month_abbr[self.open_date.month]} {self.open_date.year}".center(
            self.width - self.header_margin * 2, self.config.chars["f_hor"])
        return self.widget_title + out[len(self.widget_title):]

    def update(self):
        super().update()
        self.reload_data()

    def reload_data(self):
        if session_config.IOConfig.event_file.is_file():
            with open(session_config.IOConfig.event_file, "rb") as file:
                try:
                    CalendarOutliner.timetable.load_pickle(file)
                except EOFError:
                    CalendarOutliner.timetable = EventCalendar()

    def toggle_deadlines(self):
        self.show_tasks = not self.show_tasks

    def _dump_events(self):
        with open(session_config.IOConfig.event_file, "wb") as file:
            pickle.dump(self.timetable.daytables_by_date, file)

    def add_entry(self):
        date_str = self.input_manager.recieve_text("Add new event on (dd or dd/mm/yyyy): ", split_mask="__/__/____")
        if 0 < len(date_str) <= 2:
            new_event_date = self.open_date.replace(day=int(date_str))
        elif len(date_str) == 10:
            date_str = date_str.split("/")
            new_event_date = datetime.date(int(date_str[2]), int(date_str[1]), int(date_str[0]))
        else:
            return False

        time_str = self.input_manager.recieve_text("Enter time (hh:mm): ", split_mask="__:__")
        if len(time_str) == 5:
            time_str = time_str.split(":")
            new_event_time = datetime.time(int(time_str[0]), int(time_str[1]))
        else:
            new_event_time = None

        new_event_text = self.input_manager.recieve_text("Enter event name: ")
        if len(new_event_text) == 0:
            return False

        # TODO Switch to Timetable
        self.timetable.add_item(Event(date=new_event_date, time=new_event_time, text=new_event_text))
        self._dump_events()

    def remove_entry(self):
        date_str = self.input_manager.recieve_text("Delete event on (date): ", split_mask="__")
        if len(date_str) == 0:
            return
        date = int(date_str)
        CalendarOutliner.remove_mode = self.open_date.replace(day=date)
        self.input_manager.app.force_update_all()

        event_str = self.input_manager.recieve_text("Delete event number:")
        if len(event_str) != 0:
            event_num = int(event_str)
            self.timetable.remove_item(datetime.date(self.open_date.year, self.open_date.month, date), event_num)
            self._dump_events()
        CalendarOutliner.remove_mode = False

    def scroll(self, direction: (int, int)):
        super().scroll(direction)
        months = direction[1]
        new_month = self.open_date.month + months
        if new_month > 12 or new_month < 0:
            self.open_date = self.open_date.replace(year=self.open_date.year + (new_month // 12))
            new_month = new_month % 12
        if new_month == 0:
            self.open_date = self.open_date.replace(year=self.open_date.year - 1)
            new_month = 12
        self.open_date = self.open_date.replace(month=new_month)

    def show_today(self):
        self.open_date = datetime.date.today()

    def render(self):

        weeks = calendar.Calendar().monthdays2calendar(self.open_date.year, self.open_date.month)
        row_size = self.content_length // len(weeks)
        column_size = self.content_width // 7
        grid_gap = 1
        row = 0
        tasks = None
        if self.show_tasks:
            tasks = ioManager.load_tasks().get_all_children(with_deadline_only=True)

        for week in weeks:
            for day in week:
                if day[0] == 0:
                    continue
                # day: (day_num, weekday_num)
                cell_top = self.content_top + row * row_size
                cell_left = self.content_left + day[1] * column_size
                cell_date = datetime.date(self.open_date.year, self.open_date.month, day[0])

                # Select color
                color = session_config.ColorsConfig.generic_text_pair
                if cell_date.weekday() >= 5:
                    color = session_config.ColorsConfig.weekend_pair
                if cell_date == cell_date.today():
                    color = session_config.ColorsConfig.bright_select
                    self.stdscr.addnstr(cell_top, cell_left, " " * (column_size - grid_gap), column_size - 2, curses.color_pair(color))

                # Add a header, if necessary
                if cell_date.day <= 7:
                    cell_header = calendar.day_name[cell_date.weekday()]
                    if len(cell_header) > column_size - 3:
                        cell_header = calendar.day_abbr[cell_date.weekday()]
                    self.stdscr.addnstr(cell_top, cell_left + (column_size - len(cell_header) + 1) // 2,
                                        cell_header, column_size - 2, curses.color_pair(color))

                # Draw a date in top left corner of the cell
                self.stdscr.addnstr(cell_top, cell_left, f"{cell_date.day}", column_size - 2, curses.color_pair(color))

                # Start drawing events
                color = session_config.ColorsConfig.generic_text_pair
                event_count = 0
                if cell_date in self.timetable.event_dict.keys():
                    event_lsit = self.timetable.event_dict[cell_date]
                    for event in event_lsit:
                        event_count += 1
                        if event_count >= row_size:
                            break
                        out = f"{(str(event_count) + ' ') if cell_date == CalendarOutliner.remove_mode else event.icon}" \
                              f"{event}"
                        out += " " * (curses.COLS - len(out))
                        self.stdscr.addnstr(cell_top + event_count, cell_left, out, self.right - cell_left,
                                            curses.color_pair(color))
                if self.show_tasks:
                    color = session_config.ColorsConfig.deadline_pair
                    task_n = event_count + 1
                    for task in tasks:
                        if task.deadline != cell_date or task.importance == data.Importance.DONE:
                            continue
                        if task_n >= row_size:
                            break
                        out = f"{session_config.Icons.deadline_icon}{task.text}"
                        out += " " * (curses.COLS - len(out))
                        self.stdscr.addnstr(cell_top + task_n, cell_left, out, self.width - cell_left,
                                            curses.color_pair(color))
                        task_n += 1
            row += 1
        self.render_frame()
        self.render_header()


# TODO Rewrite AgendaOutliner, implementing V1 Interface from page 4 in the notebook
class AgendaOutliner(CalendarOutliner, TaskOutliner):
    ID = 2
    config = session_config.DayOutlinerConfig

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0):
        super().__init__(stdscr, x_offset, y_offset)
        self.open_date = datetime.date.today() + datetime.timedelta(1)

    def scroll(self, direction: (int, int)):
        TaskOutliner.scroll(self, direction)
        days = direction[1]
        self.open_date += datetime.timedelta(days=days)

    def reload_data(self):
        pass

    @property
    def today_events(self):
        if self.today in self.timetable.event_dict:
            return self.timetable.event_dict[self.today]
        else:
            return []

    @property
    def later_events(self):
        later = self.open_date
        if later in self.timetable.event_dict.keys():
            return self.timetable.event_dict[later]
        else:
            return []

    @property
    def today_tasks(self):
        tasks_with_deadline = self.root_task.get_all_children(with_deadline_only=True)
        today_tasks = []
        for task in tasks_with_deadline:
            if task.deadline == self.today:
                today_tasks.append(task)
        return today_tasks

    @property
    def later_tasks(self):
        later = self.open_date
        tasks_with_deadline = self.root_task.get_all_children(with_deadline_only=True)
        later_tasks = []
        for task in tasks_with_deadline:
            if task.deadline == later:
                later_tasks.append(task)
        return later_tasks

    @property
    def today(self):
        return datetime.date.today()

    @property
    def header(self):
        widget_title = "Agenda"
        tomorrow = datetime.date.today() + datetime.timedelta(1)
        later = self.open_date
        horizontal_size = ((self.width - 1) // 2) if self.today != later else self.width
        horizontal_size -= 2
        today_text = f"Today, {calendar.month_abbr[self.today.month]} {self.today.day}"
        later_text = ""
        if later == tomorrow:
            later_text = f"Tomorrow, {calendar.month_abbr[tomorrow.month]} {tomorrow.day}"
        elif later > tomorrow:
            later_text = f"Later, on {calendar.month_abbr[later.month]} {later.day}"
        elif later < self.today:
            later_text = f"Previously, on {calendar.month_abbr[later.month]} {later.day}"
        out = today_text.center(horizontal_size, self.config.chars["f_hor"])
        if len(later_text) > 0:
            out += later_text.center(horizontal_size - self.header_margin * 2, self.config.chars["f_hor"])
        out = widget_title + out[len(widget_title):]
        return out

    def render(self):
        columns = (self.open_date != self.open_date.today()) + 1
        column_width = self.content_width // columns

        tasks_header = "Tasks-due".center(column_width, "-")
        events_header = f"Events".center(column_width, "-")
        divider = "·"

        events = self.today_events, self.later_events
        tasks = self.today_tasks, self.later_tasks

        color = session_config.ColorsConfig.generic_text_pair

        max_events = max(len(events[0]), len(events[1]))
        max_tasks = max(len(tasks[0]), len(tasks[1]))

        combined_lists = events, tasks
        max_combined = max_events, max_tasks
        header_combined = events_header, tasks_header

        line_count = 0  # used for calculating self.line_count to limit scrolling

        for column in range(columns):
            line = 0 - self.start_line
            for block in range(2):

                # Draw header, if necessary
                if len(combined_lists[block][column]) > 0:
                    if self.content_length >= line >= 0:
                        self.stdscr.addnstr(self.content_top + line, self.content_left + column_width * column,
                                            header_combined[block],
                                            column_width, curses.color_pair(color))
                    line += 1

                # Draw contents of a block (events or tasks)
                for index in range(max_combined[block]):
                    if index < len(combined_lists[block][column]):

                        if block == 0:
                            event = events[column][index]
                            if self.content_length >= line >= 0:
                                output = f"""{(str(index + 1) + ' ') if event.date == CalendarOutliner.remove_mode
                                else event.icon}""" + \
                                         (event.time.strftime('%H:%M') +
                                          ' ' if event.time is not None else '') + event.text
                                self.stdscr.addnstr(self.content_top + line, self.content_left + column_width * column,
                                                    output,
                                                    column_width, curses.color_pair(color))

                        if block == 1:
                            task: TaskNode = tasks[column][index]
                            if self.content_length >= line >= 0:
                                self.stdscr.addnstr(self.content_top + line, self.content_left + column_width * column,
                                                    task.to_cli_format(),
                                                    column_width, curses.color_pair(color))

                        line += 1

                # If there was an events block, add an empty line to visually separate it from tasks
                if len(combined_lists[block][column]) > 0:
                    line += 1

            line_count = max(line + self.start_line - 1, line_count)

        self.line_count = line_count

        # Draw divider
        if columns == 2:
            center = self.content_left + (self.content_width // 2 - 1)
            for y in range(self.content_length):
                self.stdscr.addnstr(self.content_top + y, center, divider, 1, curses.color_pair(color))

        self.render_frame()
        self.render_header()


class DayplanOutliner(Outliner):

    def __init__(self, stdscr: curses.window):
        super().__init__(stdscr)
        self.header = "Plan For Today"






    ''' DayplanOutliner UI model
        _________________________________________________
        | 12:15                              28/10/2023 |
        |                                               |
        |  #####|############=====|=========|=========  |
        |       ^                 ^         ^           |
        | Now Doing: *work name*                        |
        |_______________________________________________| '''
    def render(self):

        # Render time string
        # TODO Make the entire TUI async and event based. Oh fuck

        # Render date string

        # Render progressbar

        # Render current active

        self.render_decoration()