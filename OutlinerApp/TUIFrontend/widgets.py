import curses

from .data import Point
from .data import Bounds

from ..Backend.configs import session_config


def render_msg(stdscr: curses.window, text: str):
    stdscr.addnstr(curses.LINES - 1, 0, " " * curses.COLS, curses.COLS - 1)
    stdscr.addnstr(curses.LINES - 1, 0, text, curses.COLS)
    stdscr.refresh()
    stdscr.getch()


class Widget:
    margins: tuple[int, int]
    _fixed_width: bool | int
    _fixed_length: bool | int
    config: session_config.WidgetConfig
    is_focused: bool = False
    is_open = True
    is_root_window: bool = False
    header: str = None
    name: str
    ID = None

    @staticmethod
    def reload_data():
        pass

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0, input_manager=None):
        super().__init__()
        self.config = session_config.WidgetConfig
        self.margins = self.config.margins
        self._fixed_width = False
        self._fixed_length = False
        self.stdscr = stdscr
        self.is_framed = True
        self.left = x_offset
        self.top = y_offset
        self.input_manager = input_manager

    @property
    def name(self):
        return str(type(self).__name__)

    @property
    def fixed_width(self):
        return self._fixed_width

    @fixed_width.setter
    def fixed_width(self, val):
        self._fixed_width = val

    @property
    def fixed_length(self):
        return self._fixed_length

    @fixed_length.setter
    def fixed_length(self, val):
        self._fixed_length = val

    @property
    def width(self):
        width = curses.COLS
        if self.fixed_width:
            width = self.fixed_width
        if width + self.left > curses.COLS or width < 0:
            width = curses.COLS - self.left
        return width

    @property
    def length(self):
        return self.fixed_length if self.fixed_length else curses.LINES

    @property
    def right(self):
        return self.left + self.width - 1

    @right.setter
    def right(self, val):
        self.fixed_width = val-self.left

    @property
    def bottom(self):
        return self.top + self.length - 1

    @bottom.setter
    def bottom(self, val):
        self.fixed_length = val-self.top

    @property
    def content_width(self):
        return self.width - self.margins[1] - 2 * self.is_framed

    @property
    def content_length(self):
        return self.length - self.margins[0] - 2 * self.is_framed

    @property
    def content_top(self):
        return self.top + self.margins[0] + self.is_framed

    @property
    def content_left(self):
        return self.left + self.margins[1] + self.is_framed

    @property
    def bounds(self):
        return Bounds(left=self.left,top=self.top,right=self.right,bottom=self.bottom)

    @property
    def center(self):
        return Point(self.width//2, self.length//2)

    def focus(self):
        self.is_focused = True

    def unfocus(self):
        self.is_focused = False

    def render(self):
        pass

    def update(self):
        self.stdscr.redrawwin()
        self.render()

    def render_decoration(self,color = None):
        if self.is_framed:
            self.render_frame(color)
        if self.header is not None:
            self.render_header(color)

    def render_header(self, color=None):
        pass

    def render_frame(self, color = None):
        chars = self.config.chars

        if color is None:
            if self.is_focused:
                color = curses.color_pair(session_config.ColorsConfig.selected_pair)
            else:
                color = curses.color_pair(session_config.ColorsConfig.generic_text_pair)
        else:
            color = curses.color_pair(color)
        line = chars["f_top_left"] + \
            chars["f_hor"] * (self.width - 2) + \
            chars["f_top_right"]
        self.stdscr.addstr(self.top, self.left, line, color)

        for y in range(self.top + 1, self.bottom):
            self.stdscr.addstr(y, self.left, chars["f_vert"], color)
            self.stdscr.addstr(y, self.right, chars["f_vert"], color)
        try:
            line = chars["f_bottom_left"] + chars["f_hor"] * (self.left + self.width - self.left - 2) \
                   + chars[
                       "f_bottom_right"]
            self.stdscr.addstr(self.bottom, self.left, line, color)
        except curses.error:
            pass


