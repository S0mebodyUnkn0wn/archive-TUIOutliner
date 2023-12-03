import calendar
import curses
import datetime
import time

from .overlays import EditFieldsOverlay
from .widgets import Widget, Header
from ..Backend import data
from ..Backend import ioManager
from ..Backend.configs import session_config
from ..Backend.tasks import TaskNode
from ..Backend.timetables import TimetableItem, TimetableTask


class Outliner(Widget):
    config = session_config.OutlinerConfig
    remove_mode = False

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0, input_manager=None):
        super().__init__(stdscr, x_offset, y_offset, input_manager)
        self.margins = self.config.margins
        self.fixed_width = self.config.fixed_width
        self.fixed_length = self.config.fixed_length

    def add_entry(self):
        """
        Starts a process of adding an entry to the outliner

        *Implementation details:*
            * Should be a wrapper calling outliner's add method
        """
        pass

    def scroll(self, direction: (int, int)):
        pass

    def remove_entry(self):
        """
        Starts a process of removing an entry to the outliner

        *Implementation details:*
            * Should be a wrapper calling outliner's remove method
        """
        pass

    @property
    def header(self):
        return Header(f"Outliner")

    def edit_entry(self):
        """
        Starts a process of editing an entry of the outliner

        *Implementation details:*
            * Should be a wrapper calling outliner's edit method
        """
        pass


class TaskOutliner(Outliner):
    tasks: list[TaskNode]
    config = session_config.TaskOutlinerConfig
    ID = 0

    @staticmethod
    def reload_data():
        TaskOutliner.tasks = ioManager.get_root_task().get_all_children()

    @staticmethod
    def toggle_hide_done():
        # TODO Questionable implementation
        if data.Importance.DONE in session_config.TaskConfig.exclude_tasks:
            session_config.TaskConfig.exclude_tasks.remove(data.Importance.DONE)
        else:
            session_config.TaskConfig.exclude_tasks.append(data.Importance.DONE)

    @staticmethod
    def _select_color(task) -> int:
        """Selects a color pair for the supplied task in accordance with task's importance and status
        :returns: suitable color pair number"""
        color = session_config.ColorsConfig.generic_text_pair
        if task.importance == data.Importance.DONE:
            color = session_config.ColorsConfig.done_pair
        elif data.Importance.DOING_C <= task.importance <= data.Importance.DOING_A:
            color = session_config.ColorsConfig.doing_pair
        elif data.Importance.WAITING_C <= task.importance <= data.Importance.WAITING_A:
            color = session_config.ColorsConfig.waiting_pair
        return color

    def __init__(self, stdscr: curses.window, app, x_offset=0, y_offset=0):
        super().__init__(stdscr, app, x_offset, y_offset)
        self.config = session_config.TaskOutlinerConfig
        self.start_line = 0
        self.reload_data()

    @property
    def line_count(self):
        return len(TaskOutliner.tasks)

    @property
    def header(self):
        return Header(f"TODO List")

    def scroll(self, direction: (int, int)):
        super().scroll(direction)
        lines = direction[0]
        if 0 <= self.start_line + lines < self.line_count:
            self.start_line += lines

    def add_entry(self):
        self.add_task()

    def remove_entry(self):
        self.remove_task()

    def edit_entry(self):
        self.edit_task()

    def add_task(self, root_task=None) -> TaskNode | None:
        """Prompts the user to create a new task, if the user enters valid data for all prompts a new task is added to the to-do list
        :returns: newly created TaskNode if the user has created a new task, None if the user has stopped the process prematurely
        """
        if root_task is None:
            root_task = ioManager.get_root_task()
        task_text = self.input_manager.recieve_text("Enter task: ")
        if len(task_text) == 0:
            return None

        deadline_str = self.input_manager.recieve_text("Enter task deadline (dd/mm/yyyy): ", split_mask="__/__/____")
        if len(deadline_str) == 10:
            deadline_str: str
            deadline_str = deadline_str.split("/")
            task_deadline = datetime.date(int(deadline_str[2]), int(deadline_str[1]), int(deadline_str[0]))
        else:
            task_deadline = None
        new_task = TaskNode(text=task_text, deadline=task_deadline)
        return ioManager.add_subtask(new_task, root_task)

    def create_subtask(self) -> TaskNode | None:
        """Prompts the user to create a subtask of a task, if a task is selected, prompts user to create a task that will be a subtask of the selected task
        :returns: newly created TaskNode if the user selected and then created a new task, None if the user has stopped the process prematurely
        """
        task = self.select_task("Create a subtask for task number:")
        if task is not None:
            return self.add_task(task)
        return None

    def remove_task(self) -> TaskNode | None:
        """Prompts the user to mark a task as done, if a task is selected, it is deleted from the to-do list
        :returns: removed TaskNode if user selected a task, None if user chose not to select a task
        """
        task = self.select_task("Delete task number:")
        if task is not None:
            ioManager.remove_task(task)
        return task

    def mark_done(self) -> TaskNode | None:
        """Prompts the user to mark a task as done, if a task is selected, toggles its done status
        :returns: modified TaskNode if user selected a task, None if user chose not to select a task
        """
        task = self.select_task(prompt="Mark as done task number:")
        if task is not None:
            ioManager.mark_done(task)
        return task

    def edit_task(self) -> TaskNode | None:
        """Prompts the user to select and edit a task, if a task selected opens up an edit overlay
        :returns: modified TaskNode, None if user did not select a task"""
        task = self.select_task(prompt="Edit task number:")
        if task is None:
            return None

        # TODO TMP IMPLEMENTATION CHANGE TO OVERLAYS ASAP
        task_text = self.input_manager.recieve_text("Edit task text: ", prefill=task.text)
        if len(task_text) == 0 or task.text == task_text:
            task_text = None

        if task.deadline is not None:
            current_deadline = f"{task.deadline.day}/{task.deadline.month}/{task.deadline.year}"
        else:
            current_deadline = ""
        deadline_str = self.input_manager.recieve_text("Edit task deadline (dd/mm/yyyy): ", split_mask="__/__/____", prefill=current_deadline)
        if len(deadline_str)==0:
            task_deadline = ""
        elif deadline_str!=current_deadline:
            deadline_str: str
            deadline_str = deadline_str.split("/")
            task_deadline = datetime.date(int(deadline_str[2]), int(deadline_str[1]), int(deadline_str[0]))
        else:
            task_deadline = None
        return ioManager.edit_task(task, task_text, task_deadline)

    def select_task(self, prompt: str) -> TaskNode | None:
        """Prompts the user to select a task from ones diplayed by the outliner
        :returns: TaskNode if user selected a task, None if user chose not to select a task
        """
        TaskOutliner.remove_mode = True
        self.renderer.update()

        task_str = self.input_manager.recieve_text(prompt)
        TaskOutliner.remove_mode = False
        if len(task_str) != 0 and task_str != "\n":
            task_num = int(task_str)
            if 1 <= task_num <= len(self.tasks):
                return self.tasks[task_num - 1]
        return None

    def render(self):
        """Prepares render of the current state of the TaskOutliner, does not refresh the screen"""

        line = -1 - self.start_line

        for task in self.tasks:
            line += 1
            if not self.content_length >= line >= 0:
                continue
            output = f"{(str(self.tasks.index(task) + 1) + ' ') if TaskOutliner.remove_mode else ''}" \
                     f"{task}"
            right_limit = self.content_right
            if task.deadline is not None:
                right_limit = self._render_deadline(line, task)
            if self.content_left + len(output) >= right_limit:
                output = output[0:right_limit - self.content_left - 4]
                output += "..."

            color = self._select_color(task)
            self.renderer.render_string(output, self.content_top + line, self.content_left, self.content_width, color)

        self.render_decorations()
        self.window.syncup()

    def _render_deadline(self, line, task):
        if task.importance == data.Importance.DONE:
            color = session_config.ColorsConfig.done_pair
        elif task.deadline < datetime.date.today():
            color = session_config.ColorsConfig.selected_pair
        else:
            color = session_config.ColorsConfig.deadline_pair
        deadline = session_config.Icons.deadline_icon + task.deadline.strftime("%d/%m/%Y")
        right_limit = self.content_right - len(deadline)

        self.renderer.render_string(deadline, self.content_top + line, self.content_right - len(deadline), self.content_width, color)

        return right_limit


class CalendarOutliner(Outliner):
    config = session_config.EventOutlinerConfig
    widget_title = "Events"
    show_tasks = True
    ID = 1

    def __init__(self, stdscr: curses.window, app, x_offset=0, y_offset=0):
        super().__init__(stdscr, app, x_offset, y_offset)
        self.open_date = datetime.date.today()
        self.reload_data()

    @property
    def header(self):
        out = f"{calendar.month_abbr[self.open_date.month]} {self.open_date.year}".center(
            self.width - self.header_margin * 2, self.config.chars["f_hor"])
        return Header(self.widget_title + out[len(self.widget_title):])

    def toggle_deadlines(self):
        self.show_tasks = not self.show_tasks

    def add_entry(self):
        self.add_event()

    def remove_entry(self):
        self.remove_event()

    def edit_entry(self):
        self.edit_event()

    def select_event(self, action_prompt: str = "Select") -> TimetableItem | None:
        date_str = self.input_manager.recieve_text(f"{action_prompt} event on (date): ", split_mask="__")
        if len(date_str) == 0:
            return
        date = int(date_str)
        CalendarOutliner.remove_mode = self.open_date.replace(day=date)
        self.renderer.update()

        event_str = self.input_manager.recieve_text(f"{action_prompt} event number: ")
        CalendarOutliner.remove_mode = False
        date = self.open_date.replace(day=date)
        if len(event_str) != 0:
            event_num = int(event_str)
            return ioManager.get_timetable().find_item(date, event_num - 1)

    def edit_event(self):
        event = self.select_event("Edit")
        if event is None:
            return
        date_str = self.input_manager.recieve_text("Edit event date (dd or dd/mm/yyyy): ", split_mask="__/__/____", prefill=event.date.strftime("%d/%m/%Y"))
        if 0 < len(date_str) <= 2:
            new_event_date = self.open_date.replace(day=int(date_str))
        elif len(date_str) == 10:
            date_str = date_str.split("/")
            new_event_date = datetime.date(int(date_str[2]), int(date_str[1]), int(date_str[0]))
        else:
            return False

        time_str = self.input_manager.recieve_text("Edit event time (hh:mm): ", split_mask="__:__", prefill=event.start_time.strftime("%H:%M"))
        if len(time_str) == 5:
            time_str = time_str.split(":")
            new_event_time = datetime.time(int(time_str[0]), int(time_str[1]))
        else:
            new_event_time = None

        new_event_text = self.input_manager.recieve_text("Edit event name: ",prefill=event.name)
        if len(new_event_text) == 0:
            return False

        new_event = TimetableItem(date=new_event_date, name=new_event_text)
        new_event.start_time = new_event_time
        ioManager.edit_event(event, new_event)

    def add_event(self):
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

        new_event = TimetableItem(date=new_event_date, name=new_event_text)
        new_event.start_time = new_event_time
        ioManager.add_to_timetable(new_event)

    def remove_event(self):
        event = self.select_event("Delete")
        ioManager.remove_from_timetable(event)

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

        for week in weeks:
            for day in week:
                if day[0] == 0:
                    continue
                self._render_cell(column_size, day, grid_gap, row, row_size)
            row += 1
        self.render_decorations()
        self.window.syncup()

    def _render_cell(self, column_size, day, grid_gap, row, row_size):
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
            self.window.addnstr(cell_top, cell_left, " " * (column_size - grid_gap), column_size - 2, curses.color_pair(color))

        # Add a header, if necessary
        if cell_date.day <= 7:
            cell_header = calendar.day_name[cell_date.weekday()]
            if len(cell_header) > column_size - 3:
                cell_header = calendar.day_abbr[cell_date.weekday()]
            self.window.addnstr(cell_top, cell_left + (column_size - len(cell_header) + 1) // 2,
                                cell_header, column_size - 2, curses.color_pair(color))

        # Draw a date in top left corner of the cell
        self.window.addnstr(cell_top, cell_left, f"{cell_date.day}", column_size - 2, curses.color_pair(color))

        # Start drawing events
        color = session_config.ColorsConfig.generic_text_pair
        event_count = 0

        # If there are no events, there's nothing to draw
        if cell_date not in ioManager.get_timetable().daytables_by_date.keys():
            return
        timetable = ioManager.get_timetable()
        event_lsit = timetable.daytables_by_date[cell_date]
        # Same as above
        if len(event_lsit) == 0:
            return

        for event in event_lsit:
            event_count += 1
            if event_count >= row_size:
                break
            if isinstance(event, TimetableTask):
                if not self.show_tasks: continue
                if event.task.is_done:
                    out = f"{session_config.Icons.done_icon}"
                    color = session_config.ColorsConfig.done_pair
                else:
                    out = f"{session_config.Icons.deadline_icon}"
                    color = session_config.ColorsConfig.deadline_pair
                out += f"{event.task.text}"
            else:
                out = f"{(str(event_count) + ' ') if cell_date == CalendarOutliner.remove_mode else event.icon}" \
                      f"{str(event)}"
            out += " " * (curses.COLS - len(out))
            self.window.addnstr(cell_top + event_count, cell_left, out, self.right - cell_left,
                                curses.color_pair(color))


# TODO Rewrite AgendaOutliner, implementing V1 Interface from page 4 in the notebook
class AgendaOutliner(CalendarOutliner, TaskOutliner):
    ID = 2
    config = session_config.DayOutlinerConfig
    line_count: int = 0

    def __init__(self, stdscr: curses.window, app, x_offset=0, y_offset=0):
        super().__init__(stdscr, app, x_offset, y_offset)
        self.open_date = datetime.date.today() + datetime.timedelta(1)

    def scroll(self, direction: (int, int)):
        TaskOutliner.scroll(self, direction)
        days = direction[1]
        self.open_date += datetime.timedelta(days=days)

    def add_entry(self):
        mode: str = self.input_manager.recieve_text("Would you like to add a [T]ask or an [E]vent? ")
        if len(mode) == 0:
            return
        match (mode[0].lower()):
            case "t":
                self.add_task()
            case "e":
                self.add_event()
            case _:
                return

    def remove_entry(self):
        mode: str = self.input_manager.recieve_text("Would you like to remove [T]ask or an [E]vent? ")
        if len(mode) == 0:
            return
        match (mode[0].lower()):
            case "t":
                self.remove_task()
            case "e":
                self.remove_event()
            case _:
                return

    def reload_data(self):
        pass

    @property
    def today_events(self) -> list[TimetableItem]:
        if self.today in ioManager.get_timetable().daytables_by_date:
            return ioManager.get_timetable().daytables_by_date[self.today]
        else:
            return []

    @property
    def later_events(self) -> list[TimetableItem]:
        later = self.open_date
        if later in ioManager.get_timetable().daytables_by_date.keys():
            return ioManager.get_timetable().daytables_by_date[later]
        else:
            return []

    @property
    def today_tasks(self):
        tasks_with_deadline = ioManager.get_root_task().get_all_children(with_deadline_only=True)
        today_tasks = []
        for task in tasks_with_deadline:
            if task.deadline == self.today:
                today_tasks.append(task)
        return today_tasks

    @property
    def later_tasks(self):
        later = self.open_date
        tasks_with_deadline = ioManager.get_root_task().get_all_children(with_deadline_only=True)
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
        out = today_text.center(horizontal_size - 1, self.config.chars["f_hor"])
        if len(later_text) > 0:
            out += later_text.center(horizontal_size - self.header_margin * 2, self.config.chars["f_hor"])
        out = widget_title + out[len(widget_title):]
        return Header(out)

    def render(self):
        columns = (self.open_date != self.open_date.today()) + 1
        column_width = self.content_width // columns

        divider = "·"

        events = self.today_events, self.later_events

        color = session_config.ColorsConfig.generic_text_pair

        line_count = 0  # used for calculating self.line_count to limit scrolling

        for column in range(columns):
            line = 0 - self.start_line

            # Draw contents of a block (events or tasks)
            for index in range(len(events)):
                if index >= len(events[column]):
                    continue
                event: TimetableItem = events[column][index]
                if self.content_length >= line >= 0:
                    output = f"""{(str(index + 1) + ' ') if event.date == CalendarOutliner.remove_mode else event.icon}""" + \
                             (event.start_time.strftime('%H:%M') + ' ' if event.start_time is not None else '') + event.name
                    self.renderer.render_string(output, self.content_top + line, self.content_left + column_width * column, column_width, color)

                line += 1

            line_count = max(line + self.start_line - 1, line_count)

        self.line_count = line_count

        # Draw a divider
        if columns == 2:
            center = self.content_left + (self.content_width // 2 - 1)
            for y in range(self.content_length):
                self.window.addnstr(self.content_top + y, center, divider, 1, curses.color_pair(color))

        self.render_decorations()
        self.window.syncup()


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

        self.render_decorations()
