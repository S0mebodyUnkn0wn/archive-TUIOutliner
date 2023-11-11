import curses

from . import widgets
from .widgets import Widget, Header
from ..Backend.configs import session_config

# TODO Overlays can have a container attribute that defines a widget (or whole window) they should be contained within


class Overlay(widgets.Widget):

    def __init__(self, stdscr: curses.window):
        super().__init__(stdscr)
        self.config = session_config.WidgetConfig
        self.margins = (1, 1)
        self.is_framed = False

    @property
    def fixed_width(self):
        return self._fixed_width

    @fixed_width.setter
    def fixed_width(self, val):
        self._fixed_width = val
        self.left = curses.COLS // 2 - self.width//2

    @property
    def fixed_length(self):
        return self._fixed_length

    @fixed_length.setter
    def fixed_length(self, val):
        self._fixed_length = val
        self.top = curses.LINES // 2 - self.length // 2

    def render_header(self, color=None):
        if color is None:
            color = session_config.ColorsConfig.overlay_text_pair

        self.window.addnstr(self.top, self.left, self.header.center(self.width), self.width, curses.color_pair(color))

    def render(self):
        color = session_config.ColorsConfig.overlay_text_pair
        for y in range(self.top,self.bottom):
            self.window.addnstr(y, self.left, " " * self.width, self.width, curses.color_pair(color))

        self.render_decorations()


class OpenNewOverlay(Overlay):

    def __init__(self, stdscr: curses.window, available_widgets):
        super().__init__(stdscr)
        self.fixed_length=20
        self.fixed_width=70
        self.header: Header = Header("Open New Widget", align="center")
        self.available_widgets: list[type(Widget)] = available_widgets
        self.closed_widgets: list[type(Widget)] = self.available_widgets
        self.selected_line: int = 0

    def get_closed(self):
        for widget in self.available_widgets:
            if not widget.is_open:
                self.closed_widgets.append(type(widget))

    def scroll(self, line):
        if 0<=self.selected_line + line<len(self.closed_widgets):
            self.selected_line += line

    def render(self):
        super().render()
        for index in range(len(self.closed_widgets)):
            color = session_config.ColorsConfig.overlay_text_pair
            if index==self.selected_line:
                color = session_config.ColorsConfig.bright_select
            self.window.addnstr(self.content_top + index, self.content_left, self.closed_widgets[index].__name__, self.content_width, curses.color_pair(color))