import configparser
import curses
import dataclasses
from dataclasses import dataclass
from pathlib import Path

from . import data


@dataclass
class _IO:
    logseq_dir: Path = Path("~/Documents/logseq/St-Andrews-uni").expanduser()
    tasks_file: Path = Path("~/ProgrammingProjects/PycharmProjects/TUICalendar/tasks.pkl").expanduser()
    calcure_file: Path = Path("~/.config/calcure/tasks.csv").expanduser()
    event_file: Path = Path("~/ProgrammingProjects/PycharmProjects/TUICalendar/events.pkl").expanduser()


@dataclass
class _Task:
    tab_string: str = "  "
    exclude_tasks: list[data.Importance] = dataclasses.field(default_factory=lambda: [data.Importance.DONE])
    keywords: tuple = ("TODO", "DOING", "DONE", "WAITING")


@dataclass
class _Event:
    pass


@dataclass
class _App:
    pass


@dataclass
class _Widget:
    content_path: str = None
    margins: tuple[int, int] = (0, 0)
    chars: dict[str, str] = dataclasses.field(default_factory=lambda: {
        "f_vert": "│",
        "f_hor": "─",
        "f_top_right": "┐",
        "f_bottom_right": "┘",
        "f_top_left": "┌",
        "f_bottom_left": "└"
    })
    fixed_width: bool | int = False
    fixed_length: bool | int = False


@dataclass
class _Outliner(_Widget):
    pass


@dataclass
class _TaskOutliner(_Outliner):
    content_path: str = _IO.tasks_file


@dataclass
class _EventOutliner(_Outliner):
    content_path: str = _IO.event_file
    lines_per_day: int = 4


@dataclass
class _DayOutliner(_Outliner):
    content_path: str = _IO.event_file


@dataclass
class _Colors:
    _generic_text_color: int = curses.COLOR_WHITE
    _generic_background_color: int = -1
    _overlay_background_color: int = 0

    _doing_color: int = curses.COLOR_RED
    _done_color: int = curses.COLOR_GREEN
    _deadline_color: int = curses.COLOR_YELLOW
    _waiting_color: int = 8

    _today_color: int = curses.COLOR_RED
    _weekend_color: int = curses.COLOR_CYAN

    _selected_color: int = curses.COLOR_RED

    _alt_selected_color: int = curses.COLOR_MAGENTA

    selected_pair = 16
    alt_selected_pair = 17

    generic_text_pair = 21
    doing_pair = 22
    done_pair = 23
    deadline_pair = 24
    waiting_pair = 25

    bright_select = 31
    weekend_pair = 32

    overlay_text_pair = 41
    overlay_selected_pair = 46

    def start_colors(self):
        if curses.COLORS > 8:
            curses.init_pair(self.generic_text_pair, self._generic_text_color, self._generic_background_color)
            curses.init_pair(self.doing_pair, self._doing_color, self._generic_background_color)
            curses.init_pair(self.done_pair, self._done_color, self._generic_background_color)
            curses.init_pair(self.deadline_pair, self._deadline_color, self._generic_background_color)
            curses.init_pair(self.waiting_pair, self._waiting_color, self._generic_background_color)

            curses.init_pair(self.bright_select, self._generic_background_color, self._today_color)
            curses.init_pair(self.weekend_pair, self._weekend_color, self._generic_background_color)

            curses.init_pair(self.selected_pair, self._selected_color, self._generic_background_color)
            curses.init_pair(self.alt_selected_pair, self._alt_selected_color, self._generic_background_color)

            curses.init_pair(self.overlay_text_pair, self._generic_text_color, self._overlay_background_color)
        else:
            self._generic_background_color = 0
            curses.init_pair(self.generic_text_pair, self._generic_text_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.doing_pair, self._doing_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.done_pair, self._done_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.deadline_pair, self._deadline_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.waiting_pair, self._waiting_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.bright_select, self._generic_background_color % 8, self._today_color % 8)
            curses.init_pair(self.weekend_pair, self._weekend_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.selected_pair, self._selected_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.alt_selected_pair, self._alt_selected_color % 8, self._generic_background_color % 8)
            curses.init_pair(self.overlay_text_pair, self._generic_text_color % 8, self._overlay_background_color % 8)


@dataclass
class _Calendar:
    pass


@dataclass
class Partition:
    horizontal: int = 0
    vertical: int = 0
    separation: int = 1


@dataclass
class _IconList:
    done_icon: str = " "
    deadline_icon: str = "due on "
    generic_task_icon: str = " "
    doing_icon: str = " "
    generic_task_A_icon: str = " ﰷ"
    generic_task_C_icon: str = " ﰮ"
    doing_A_icon: str = " ﰶ"
    doing_C_icon: str = " ﰭ"
    generic_event_icon: str = "• "


class ConfigManager:
    _locations = (Path(__file__, "../config.ini").resolve(),
                  Path(__file__, "../../Config/config.ini").resolve(),
                  Path(__file__, "../../../data/config.ini").resolve()
                  # Path(Path.home(),".config/TUICalendar/config.ini").resolve()
                  )

    def __init__(self):
        self.IOConfig = _IO()
        self.TaskConfig = _Task()
        self.EventConfig = _Event()
        self.AppConfig = _App()
        self.WidgetConfig = _Widget()
        self.OutlinerConfig = _Outliner()
        self.TaskOutlinerConfig = _TaskOutliner()
        self.EventOutlinerConfig = _EventOutliner()
        self.DayOutlinerConfig = _DayOutliner()
        self.ColorsConfig = _Colors()
        self.WindowPartition = Partition()
        self.Icons = _IconList
        self.reparse_config()

    def start_colors(self):
        self.ColorsConfig.start_colors()

    def reparse_config(self):
        parser = configparser.ConfigParser()
        parser.read(self._locations)

        # FilePaths
        section = "FilePaths"
        logseq_dir = Path(parser.get(section, "logseq_dir")).expanduser().resolve()
        tasks_file = Path(parser.get(section, "tasks_file")).expanduser().resolve()
        event_file = Path(parser.get(section, "event_file")).expanduser().resolve()
        # Optional
        calcure_file = Path()
        try:
            calcure_file = Path(parser.get(section, "calcure_file")).expanduser().resolve()
        except configparser.NoOptionError:
            pass

        if not logseq_dir.exists():
            raise RuntimeError(str(logseq_dir) + " does not exist")
        if not tasks_file.exists():
            raise RuntimeError(str(tasks_file) + " does not exist")
        if not calcure_file.is_file():
            self.IOConfig.calcure_file = Path()
        if not event_file.exists():
            raise RuntimeError(str(event_file) + " does not exist")

        self.IOConfig.logseq_dir = logseq_dir
        self.IOConfig.tasks_file = tasks_file
        self.IOConfig.calcure_file = calcure_file
        self.IOConfig.event_file = event_file

        # Icons
        section = "Icons"
        if parser.has_section(section):
            self.Icons.generic_task_icon = parser.get(section, "generic_task_icon", fallback="").strip("\"\'") + " "
            self.Icons.done_icon = parser.get(section, "done_icon", fallback="").strip("\"\'") + " "
            self.Icons.doing_icon = parser.get(section, "doing_icon", fallback="").strip("\"\'") + " "
            self.Icons.deadline_icon = parser.get(section, "deadline_icon", fallback="").strip("\"\'") + " "
            self.Icons.generic_task_A_icon = parser.get(section, "generic_task_A_icon", fallback="").strip("\"\'") + " "
            self.Icons.generic_task_C_icon = parser.get(section, "generic_task_C_icon", fallback="").strip("\"\'") + " "
            self.Icons.doing_A_icon = parser.get(section, "doing_A_icon", fallback="").strip("\"\'") + " "
            self.Icons.doing_C_icon = parser.get(section, "doing_C_icon", fallback="").strip("\"\'") + " "
            self.TaskConfig.tab_string = parser.get(section, "task_tab_string", fallback="  ").strip("\"\'")

        # Widgets
        section = "Widgets"
        if parser.has_section(section):
            self.WidgetConfig.chars["f_vert"] = parser.get(section, "frame_vertical",
                                                           fallback=_Outliner().chars["f_vert"])
            self.WidgetConfig.chars["f_hor"] = parser.get(section, "frame_horizontal",
                                                          fallback=_Outliner().chars["f_hor"])
            self.WidgetConfig.chars["f_top_right"] = parser.get(section, "frame_top_right",
                                                                fallback=_Outliner().chars["f_top_right"])
            self.WidgetConfig.chars["f_bottom_right"] = parser.get(section, "frame_bottom_right",
                                                                   fallback=_Outliner().chars["f_bottom_right"])
            self.WidgetConfig.chars["f_top_left"] = parser.get(section, "frame_top_left",
                                                               fallback=_Outliner().chars["f_top_left"])
            self.WidgetConfig.chars["f_bottom_left"] = parser.get(section, "frame_bottom_left",
                                                                  fallback=_Outliner().chars["f_bottom_left"])
            self.WidgetConfig.margins = (parser.getint(section, "content_margins_y", fallback=1),
                                         parser.getint(section, "content_margins_x", fallback=1))

        # Outliners
        section = "Outliners"
        if parser.has_section(section):
            self.OutlinerConfig.chars["f_vert"] = parser.get(section, "frame_vertical",
                                                             fallback=_Outliner().chars["f_vert"])
            self.OutlinerConfig.chars["f_hor"] = parser.get(section, "frame_horizontal",
                                                            fallback=_Outliner().chars["f_hor"])
            self.OutlinerConfig.chars["f_top_right"] = parser.get(section, "frame_top_right",
                                                                  fallback=_Outliner().chars["f_top_right"])
            self.OutlinerConfig.chars["f_bottom_right"] = parser.get(section, "frame_bottom_right",
                                                                     fallback=_Outliner().chars["f_bottom_right"])
            self.OutlinerConfig.chars["f_top_left"] = parser.get(section, "frame_top_left",
                                                                 fallback=_Outliner().chars["f_top_left"])
            self.OutlinerConfig.chars["f_bottom_left"] = parser.get(section, "frame_bottom_left",
                                                                    fallback=_Outliner().chars["f_bottom_left"])
            self.OutlinerConfig.margins = (parser.getint(section, "content_margins_y", fallback=1),
                                           parser.getint(section, "content_margins_x", fallback=1))

            self.TaskOutlinerConfig.chars["f_vert"] = parser.get(section, "task_frame_vertical",
                                                                 fallback=self.OutlinerConfig.chars["f_vert"])
            self.TaskOutlinerConfig.chars["f_hor"] = parser.get(section, "task_frame_horizontal",
                                                                fallback=self.OutlinerConfig.chars["f_hor"])
            self.TaskOutlinerConfig.chars["f_top_right"] = parser.get(section, "task_frame_top_right",
                                                                      fallback=self.OutlinerConfig.chars["f_top_right"])
            self.TaskOutlinerConfig.chars["f_bottom_right"] = parser.get(section, "task_frame_bottom_right",
                                                                         fallback=self.OutlinerConfig.chars[
                                                                             "f_bottom_right"])
            self.TaskOutlinerConfig.chars["f_top_left"] = parser.get(section, "task_frame_top_left",
                                                                     fallback=self.OutlinerConfig.chars["f_top_left"])
            self.TaskOutlinerConfig.chars["f_bottom_left"] = parser.get(section, "task_frame_bottom_left",
                                                                        fallback=self.OutlinerConfig.chars[
                                                                            "f_bottom_left"])
            self.TaskOutlinerConfig.margins = (
                parser.getint(section, "task_content_margins_y", fallback=self.OutlinerConfig.margins[0]),
                parser.getint(section, "task_content_margins_x", fallback=self.OutlinerConfig.margins[1]))

            self.EventOutlinerConfig.chars["f_vert"] = parser.get(section, "event_frame_vertical",
                                                                  fallback=self.OutlinerConfig.chars["f_vert"])
            self.EventOutlinerConfig.chars["f_hor"] = parser.get(section, "event_frame_horizontal",
                                                                 fallback=self.OutlinerConfig.chars["f_hor"])
            self.EventOutlinerConfig.chars["f_top_right"] = parser.get(section, "event_frame_top_right",
                                                                       fallback=self.OutlinerConfig.chars[
                                                                           "f_top_right"])
            self.EventOutlinerConfig.chars["f_bottom_right"] = parser.get(section, "event_frame_bottom_right",
                                                                          fallback=self.OutlinerConfig.chars[
                                                                              "f_bottom_right"])
            self.EventOutlinerConfig.chars["f_top_left"] = parser.get(section, "event_frame_top_left",
                                                                      fallback=self.OutlinerConfig.chars["f_top_left"])
            self.EventOutlinerConfig.chars["f_bottom_left"] = parser.get(section, "event_frame_bottom_left",
                                                                         fallback=self.OutlinerConfig.chars[
                                                                             "f_bottom_left"])
            self.EventOutlinerConfig.margins = (
                parser.getint(section, "event_content_margins_y", fallback=self.OutlinerConfig.margins[0]),
                parser.getint(section, "event_content_margins_x", fallback=self.OutlinerConfig.margins[1]))

            self.DayOutlinerConfig.chars["f_vert"] = parser.get(section, "agenda_frame_vertical",
                                                                fallback=self.OutlinerConfig.chars["f_vert"])
            self.DayOutlinerConfig.chars["f_hor"] = parser.get(section, "agenda_frame_horizontal",
                                                               fallback=self.OutlinerConfig.chars["f_hor"])
            self.DayOutlinerConfig.chars["f_top_right"] = parser.get(section, "agenda_frame_top_right",
                                                                     fallback=self.OutlinerConfig.chars["f_top_right"])
            self.DayOutlinerConfig.chars["f_bottom_right"] = parser.get(section, "agenda_frame_bottom_right",
                                                                        fallback=self.OutlinerConfig.chars[
                                                                            "f_bottom_right"])
            self.DayOutlinerConfig.chars["f_top_left"] = parser.get(section, "agenda_frame_top_left",
                                                                    fallback=self.OutlinerConfig.chars["f_top_left"])
            self.DayOutlinerConfig.chars["f_bottom_left"] = parser.get(section, "agenda_frame_bottom_left",
                                                                       fallback=self.OutlinerConfig.chars[
                                                                           "f_bottom_left"])
            self.DayOutlinerConfig.margins = (
                parser.getint(section, "agenda_content_margins_y", fallback=self.OutlinerConfig.margins[0]),
                parser.getint(section, "agenda_content_margins_x", fallback=self.OutlinerConfig.margins[1]))


session_config = ConfigManager()

if __name__ == '__main__':
    manager = ConfigManager()
    manager.reparse_config()
