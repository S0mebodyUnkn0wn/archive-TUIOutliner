import curses
from dataclasses import dataclass

from .data import Point
from .data import Bounds
from .renderer import Renderer

from ..Backend.configs import session_config


def render_msg(stdscr: curses.window, text: str):
    stdscr.addnstr(curses.LINES - 1, 0, " " * curses.COLS, curses.COLS - 1)
    stdscr.addnstr(curses.LINES - 1, 0, text, curses.COLS)
    stdscr.refresh()
    stdscr.getch()


@dataclass
class Header:
    text: str
    align: str = "left"

    def __str__(self):
        return self.text

class Widget:
    margins: tuple[int, int]
    renderer: "Renderer"
    _fixed_width: bool | int
    _fixed_length: bool | int
    config: session_config.WidgetConfig
    is_focused: bool = False
    is_open = True
    is_root_window: bool = False
    header: Header = None
    name: str
    ID = None

    @staticmethod
    def reload_data():
        pass

    def __init__(self, stdscr: curses.window, x_offset=0, y_offset=0, input_manager=None):
        super().__init__()
        self.config = session_config.WidgetConfig
        self.margins = self.config.margins
        self.header_margin = 2
        self._fixed_width = False
        self._fixed_length = False
        self.window = stdscr
        self.is_framed = True
        self.left = x_offset
        self.top = y_offset
        self.renderer = Renderer(self)
        self.input_manager = input_manager

    @staticmethod
    def name():
        return None

    @property
    def fixed_width(self):
        return self._fixed_width if self._fixed_width else self.window.getmaxyx()[1]

    @fixed_width.setter
    def fixed_width(self, val):
        self._fixed_width = val

    @property
    def fixed_length(self):
        return self._fixed_length if self._fixed_length else self.window.getmaxyx()[0]

    @fixed_length.setter
    def fixed_length(self, val):
        self._fixed_length = val

    @property
    def width(self):
        return self.fixed_width

    @property
    def length(self):
        return self.fixed_length

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
    def content_right(self):
        return self.content_left+self.content_width;

    @property
    def bounds(self):
        return Bounds(left=self.left,top=self.top,right=self.right,bottom=self.bottom)

    @property
    def center(self):
        return Point(self.left + self.width//2, self.top + self.length//2)

    def focus(self):
        self.is_focused = True
        self.render_decorations(color=session_config.ColorsConfig.selected_pair)

    def unfocus(self):
        self.is_focused = False
        self.render_decorations(color=session_config.ColorsConfig.generic_text_pair)


    def render(self):
        pass

    def update(self):
        self.window.redrawwin()
        self.render()

    def render_decorations(self, color = None):
        if self.is_framed:
            self.renderer.render_frame(color)
        if self.header is not None:
            self.renderer.render_header(color)






