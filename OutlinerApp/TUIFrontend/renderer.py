import curses

from ..Backend.configs import session_config

from .data import Point
from .data import Bounds


class Renderer:
    widget: "Widget"

    def __init__(self, widget: "Widget"):
        self.widget = widget

    def render_header(self, color=None):
        if color is None:
            if self.widget.is_focused:
                color = session_config.ColorsConfig.selected_pair
            else:
                color = session_config.ColorsConfig.generic_text_pair
        if self.widget.header is None:
            return
        header_str = f"{self.widget.header}"
        match self.widget.header.align:
            case "right":
                x_pos = self.widget.right - len(header_str) - self.widget.header_margin
            case "center":
                x_pos = self.widget.center.x - len(header_str)//2
            case _:
                x_pos = self.widget.left + self.widget.header_margin

        self.render_string(header_str,x=x_pos,color=color)

    def render_frame(self, color=None):
        chars = self.widget.config.chars
        if color is None:
            if self.widget.is_focused:
                color = session_config.ColorsConfig.selected_pair
            else:
                color = session_config.ColorsConfig.generic_text_pair
        line = chars["f_top_left"] + \
               chars["f_hor"] * (self.widget.width - 2) + \
               chars["f_top_right"]
        self.render_string(line, y=self.widget.top, x=self.widget.left, color=color)

        for y in range(self.widget.top + 1, self.widget.bottom):
            self.render_string(chars["f_vert"], y=y, x=self.widget.left, color=color)
            self.render_string(chars["f_vert"], y=y, x=self.widget.right, color=color)
            line = chars["f_bottom_left"] + chars["f_hor"] * (self.widget.left + self.widget.width
                                                              - self.widget.left - 2) + chars["f_bottom_right"]
            self.render_string(line, y=self.widget.bottom, x=self.widget.left, color=color)

    def render_string(self, string, y=None, x=None, width_limit=None, color=None):
        if y is None:
            y = self.widget.top
        if x is None:
            x = self.widget.left
        if width_limit is None:
            width_limit = self.widget.width - (x - self.widget.left)
        if color is None:
            color = session_config.ColorsConfig.generic_text_pair
        try:
            self.widget.window.addnstr(y, x, string, width_limit, curses.color_pair(color))
        except curses.error:
            if x == curses.COLS and y == curses.LINES:
                pass

    '''
    def render_content(self, content: str | list[str], y=None, x=None, width_limit=None, color=None):
        if y is None:
            y = self.widget.content_top
        if x is None:
            x = self.widget.content_left
        if width_limit is None:
            width_limit = self.widget.content_width - (x - self.widget.content_left)
        if color is None:
            color = session_config.ColorsConfig.generic_text_pair
        if isinstance(content, str):
            self.render_string(content, y, x, width_limit, color)
        if isinstance(content, list):
            for index in range(min(len(content), self.widget.bottom-y)):
                self.render_string(content[index],y+index,x=x,width_limit=width_limit,color=color)
    '''