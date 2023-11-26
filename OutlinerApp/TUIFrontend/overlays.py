import curses

from ..Backend.tasks import TaskNode
from . import widgets
from .widgets import Widget, Header
from ..Backend.configs import session_config

# TODO Overlays can have a container attribute that defines a widget (or whole window) they should be contained within

class Overlay(widgets.Widget):

    def __init__(self, stdscr: curses.window, app, header):
        super().__init__(stdscr, app)
        self.config = session_config.WidgetConfig
        self.margins = (1, 1)
        self.is_framed = False
        self.fixed_length = 20
        self.fixed_width = 70
        self.header: Header = header

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

    def render(self):
        color = session_config.ColorsConfig.overlay_text_pair
        for y in range(self.top,self.bottom):
            self.window.addnstr(y, self.left, " " * self.width, self.width, curses.color_pair(color))

        self.render_decorations(color=session_config.ColorsConfig.overlay_text_pair)

class EditFieldsOverlay(Overlay):

    def __init__(self, window, app, item, header: Header):
        super().__init__(window, app, header)
        self.item = item

    def render(self):
        super().render()
        if isinstance(self.item, TaskNode):
            self.renderer.render_string("Task text:",self.content_top+1,self.content_left,color=session_config.ColorsConfig.overlay_text_pair)
            self.renderer.render_string(" "+self.item.text+" ",self.content_top+2,self.content_left,color=session_config.ColorsConfig.bright_select)

            if self.item.deadline is not None:
                self.renderer.render_string("Task deadline:", self.content_top + 4, self.content_left, color=session_config.ColorsConfig.overlay_text_pair)
                self.renderer.render_string(" " + str(self.item.deadline) + " ", self.content_top + 5, self.content_left, color=session_config.ColorsConfig.bright_select)

    def _collide(self):
        pass

    def start(self):
        self.render()
        key = None
        while key not in [ord("e"), 27]:
            self.app.draw_overlay(self)
            key = self.app.stdscr.getch()
            self.render()
            if key == curses.KEY_MOUSE:
                mouse = curses.getmouse()
                if mouse[-1] == curses.BUTTON1_PRESSED:
                    pass


class SelectorOverlay(Overlay):

    def __init__(self, window: curses.window, app: "Application", items: list, header: Header):
        super().__init__(window, app, header)
        self.items: list = items
        self.selected_line: int = 0

    def scroll(self, line):
        if 0<=self.selected_line + line<len(self.items):
            self.selected_line += line

    def render(self):
        super().render()
        for index in range(len(self.items)):
            color = session_config.ColorsConfig.overlay_text_pair
            if index==self.selected_line:
                color = session_config.ColorsConfig.bright_select
            self.window.addnstr(self.content_top + index, self.content_left, self.items[index].__name__, self.content_width, curses.color_pair(color))