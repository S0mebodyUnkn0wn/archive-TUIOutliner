import calendar
import datetime

from textual.app import App, ComposeResult, RenderResult
from textual.containers import ScrollableContainer
from textual.widget import Widget
from textual.widgets import Label, Header

from ..Backend import ioManager
from ..Backend import data
from ..Backend.configs import session_config
from ..Backend.tasks import TaskNode


class TaskOutliner(Widget):
    BORDER_TITLE = "TODO List"

    tasks: list[TaskNode]
    config = session_config.TaskOutlinerConfig
    ID = 0
    @staticmethod
    def reload_data():
        TaskOutliner.tasks = ioManager.get_root_task().get_all_children()

    def __init__(self):
        super().__init__()
        self.config = session_config.TaskOutlinerConfig
        self.start_line = 0
        self.classes="outliner"
        self.can_focus_children: bool = False
        self.reload_data()

    def compose(self) -> ComposeResult:
        task_labels = [Label(str(task)) for task in self.tasks]
        yield ScrollableContainer(*task_labels, id="tasks")

    def add_task(self) -> None:
        pass


class CaledarCell(Widget):
    def __init__(self, date: datetime.date):
        super().__init__()
        self.open_date = date
        self.can_focus_children: bool = False

        self.classes = "calendar_cell"

    def compose(self) -> ComposeResult:
        yield Label(self.open_date.strftime("%d"))

        if self.open_date not in ioManager.get_timetable().daytables_by_date.keys():
            return
        timetable = ioManager.get_timetable()
        event_lsit = timetable.daytables_by_date[self.open_date]
        for event in event_lsit:
            yield Label(str(event))


class CalendarOutliner(Widget):
    BORDER_TITLE = "Calendar"

    def __init__(self):
        super().__init__()
        self.open_date = datetime.date.today()
        self.classes="outliner calendar"

    def compose(self) -> ComposeResult:
        weeks = calendar.Calendar().monthdays2calendar(self.open_date.year, self.open_date.month)

        for week in weeks:
            for day in week:
                if day[0] == 0:
                    continue
                yield CaledarCell(datetime.date(self.open_date.year,self.open_date.month,day[0]))

