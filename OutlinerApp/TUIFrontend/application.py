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

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.input_manager: userInput.InputManager = userInput.InputManager(self, self.stdscr)
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

        self.widgets = [
            TaskOutliner(self.stdscr),
            CalendarOutliner(self.stdscr),
            AgendaOutliner(self.stdscr),
        ]
        for widget in self.widgets:
            self.input_manager.regiseter_child(widget)

        self.widgets[0].focus()
        try:
            while True:
                self.update_render()
                self.input_manager.handle_input()
        except KeyboardInterrupt:
            pass
        observer.stop()
        return

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
                # space = partitioner.partition_space_spin(len(open_widgets))
                layout = partitioner.partition_space(self.widgets)
                for widget in self.widgets:
                    if not widget.is_open:
                        continue
                    bounds = layout.pop(0)
                    widget.top = bounds.top
                    widget.left = bounds.left
                    widget.right = bounds.right
                    widget.bottom = bounds.bottom
                for widget in self.widgets:
                    if widget.is_open:
                        widget.reload_data()
                        widget.render()
        except curses.error:
            pass
        self.stdscr.refresh()

    def draw_overlay(self, overlay: Overlay):
        try:
            overlay.render()
            self.stdscr.refresh()
        except curses.error:
            pass

