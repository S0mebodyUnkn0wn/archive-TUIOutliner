import curses

from watchdog.observers import Observer

from . import userInput
from .overlays import Overlay
from .widgets import Widget
from .outliners import TaskOutliner, CalendarOutliner, AgendaOutliner, DayplanOutliner
from ..Backend.configs import session_config
from . import partitioner


class Application:
    widgets: list[Widget]
    all_widgets: list[type(Widget)] = (
        TaskOutliner,
        CalendarOutliner,
        AgendaOutliner,
    )

    def __init__(self, stdscr):
        self.stdscr: curses.window = stdscr
        self.input_manager: userInput.InputManager = userInput.InputManager(self, self.stdscr)
        self.layout: list["Bounds"] = None
        self._do_update = False
        self.run()

    def run(self):
        curses.use_default_colors()
        session_config.start_colors()

        self.stdscr.clear()
        curses.curs_set(0)
        curses.mouseinterval(0)
        curses.mousemask(curses.BUTTON1_PRESSED)
        curses.set_escdelay(100)

        # ioManager.load_data()

        observer = Observer()
        observer.schedule(self.input_manager, path=session_config.IOConfig.logseq_dir, recursive=True)
        observer.schedule(self.input_manager, path=session_config.IOConfig.tasks_file, recursive=True)
        observer.schedule(self.input_manager, path=session_config.IOConfig.event_file, recursive=True)
        observer.start()

        self.widgets = []

        start_widgets = [
            TaskOutliner,
            CalendarOutliner,
            AgendaOutliner,
        ]
        for widget_class in start_widgets:
            self.add_widget(widget_class)

        self.widgets[0].focus()
        try:
            while True:
                self.update_render()
                self.input_manager.handle_input()
        except KeyboardInterrupt:
            pass
        observer.stop()
        return

    def add_widget(self, widget_class: type[Widget]):
        self.layout = partitioner.partition_space(len(self.widgets)+1)
        bounds = self.layout[-1]
        new_window = self.stdscr.subwin(bounds.length,bounds.width,bounds.top,bounds.left)
        new_widget = widget_class(new_window)
        new_widget.is_open = True
        self.widgets.append(new_widget)
        self.input_manager.regiseter_child(new_widget)
        self.enqueue_partition_update()

    def update_windows(self):
        for index in range(len(self.widgets)):
            bounds = self.layout[index]
            widget = self.widgets[index]
            widget.window.bkgdset(str(index))
            widget.window = self.stdscr.subwin(bounds.length,bounds.width,bounds.top,bounds.left)

    def enqueue_partition_update(self):
        self._do_update = True

    def force_update_all(self):
        """Force total redraw of all active windows,
        causes flickering use only when absolutely necessary"""

        self.stdscr.clear()
        self.stdscr.redrawwin()
        for widget in self.widgets:
            if widget.is_open:
                widget.update()

    def update_data_all(self):
        self.stdscr.redrawwin()
        for widget in self.widgets:
            if widget.is_open:
                widget.reload_data()

    def update_render(self):
        # TODO Refactor
        self.stdscr.erase()
        self.stdscr.redrawwin()
        try:
            if len(self.widgets) > 0:
                self.input_manager.make_root(self.widgets[0])
                for widget in self.widgets:
                    if self._do_update:
                        new_part = partitioner.partition_space(self.widgets)
                        self.layout = new_part
                        self.update_windows()
                        self._do_update=False
                    if widget.is_open:
                        widget.reload_data()
                        widget.render()
                        #widget.window.box()
        except curses.error:
            pass
        self.stdscr.refresh()

    def draw_overlay(self, overlay: Overlay):
        try:
            overlay.render()
            self.stdscr.refresh()
        except curses.error:
            pass

