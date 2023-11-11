import curses

import watchdog
from watchdog.events import FileSystemEventHandler

from . import application
from . import manual
from .data import Bounds, Point
from .outliners import TaskOutliner, CalendarOutliner
from .overlays import OpenNewOverlay
from .widgets import Widget
from ..Backend.configs import session_config


class InputManager(FileSystemEventHandler):

    def on_modified(self, event):
        event: watchdog.events.FileSystemEvent
        self.app.update_data_all()

    def __init__(self, app, window):
        self.children = []
        self.root_window = None
        self.focused: Widget = None
        self.app: application.Application = app
        self.window: curses.window = window

    def regiseter_child(self, child: Widget):
        self.children.append(child)
        child.input_manager = self
        if self.root_window is None:
            self.root_window = child

    def make_root(self, widget: Widget):
        for child in self.children:
            if child == widget:
                self.root_window = child

    def handle_input(self):
        key = self.window.getch()
        for child in self.children:
            if child.is_focused:
                self.focused = child
                break
        else:
            self.focused = self.children[0]
        # mouse events:
        if key == curses.KEY_MOUSE:
            try:
                mouse = curses.getmouse()
                if mouse[-1] == curses.BUTTON1_PRESSED:
                    window_under_mouse = self.collide(mouse[1], mouse[2])
                    if window_under_mouse is not None:
                        self.focused.unfocus()
                        window_under_mouse.focus()
            except curses.error:
                pass

        # passed through:
        if key == curses.KEY_UP:
            self.focused.scroll((-1, 0))
            return

        if key == curses.KEY_DOWN:
            self.focused.scroll((1, 0))
            return

        if key == curses.KEY_RIGHT:
            self.focused.scroll((0, 1))
            return

        if key == curses.KEY_LEFT:
            self.focused.scroll((0, -1))
            return

        if key == ord("a"):
            self.focused.add_entry()
            return

        if key == ord("r"):
            self.focused.remove_entry()
            return

        if isinstance(self.focused, TaskOutliner):
            if key == ord("h"):
                self.focused.toggle_hide_done()
                return

            if key == ord("d"):
                self.focused.mark_done()
                return

        if isinstance(self.focused, CalendarOutliner):
            if key == ord("T"):
                self.focused.show_today()
                return

            # Toggle showing task deadlines in Events
            if key == ord("t"):
                self.focused.toggle_deadlines()
                return

        # handled

        # include repartition
        self.app.enqueue_partition_update()

        if key == ord("o"):
            self.open_new()
            return

        if key == ord("W"):
            self.close_focused()
            return

        if key == ord("f"):
            self.fullscreen()
            return

        if key == ord("s"):
            self.open_all()
            return

        if key == ord("\t"):
            self.move_focus()
            return

        if key == ord("?"):
            self.show_help()
            return

        if key == ord("m"):
            self.swap_widget()
            return

        if key == curses.KEY_SRIGHT:
            self.partition_right()
            return

        if key == curses.KEY_SLEFT:
            self.partition_left()
            return

        if key == curses.KEY_SR:
            self.partition_up()
            return

        if key == curses.KEY_SF:
            self.partition_down()
            return

        if key == ord("R"):
            self.reset_partition()
            return

        if key == curses.KEY_RESIZE:
            curses.resize_term(*self.window.getmaxyx())
            return

    def show_help(self):
        self.window.clear()
        manual.HelpPage.render(self.window)
        self.window.getch()

    def move_focus(self):
        for i in range(len(self.children)):
            if self.children[i].is_focused:
                self.children[i].unfocus()
                n = i
        for j in range(n + 1, len(self.children)):
            if self.children[j].is_open:
                self.children[j].focus()
                break
        else:
            for j in range(0, n):
                if self.children[j].is_open:
                    self.children[j].focus()
                    break
            else:
                self.focused.focus()

    def open_all(self):
        for child in self.children:
            child.is_open = True

    def fullscreen(self):
        for child in self.children:
            if not child.is_focused:
                child.is_open = False

    def close_focused(self):
        self.focused: Widget
        self.focused.is_open = False
        self.app.widgets.remove(self.focused)

        self.move_focus()

    def reset_partition(self):
        session_config.WindowPartition.horizontal = 0
        session_config.WindowPartition.vertical = 0

    def partition_down(self):
        for child in self.children:
            if child.is_focused:
                session_config.WindowPartition.vertical += 1

    def partition_up(self):
        for child in self.children:
            if child.is_focused:
                session_config.WindowPartition.vertical -= 1

    def partition_left(self):
        session_config.WindowPartition.horizontal -= 1

    def partition_right(self):
        session_config.WindowPartition.horizontal += 1

    def display_prompt(self, prompt: str, color=session_config.ColorsConfig.generic_text_pair):
        try:
            self.window.addnstr(curses.LINES - 1, 0, prompt, curses.COLS, curses.color_pair(color))
        except curses.error:
            pass

    def recieve_text(self, prompt: str, split_mask=None) -> str:
        out = ""
        cursor = "_"
        key = None
        while key not in [ord("\n"), curses.KEY_ENTER]:
            self.display_prompt(cursor + " " * curses.COLS)
            self.display_prompt(f"{prompt}{out}{cursor}")
            key = self.window.getch()
            if key == curses.KEY_BACKSPACE:
                out = out[:len(out) - 1]
                continue
            if key == curses.KEY_EXIT or key == 27:
                return ""
            if chr(key).isalnum() or chr(key) == " ":
                if split_mask is not None:
                    if len(out) + 1 > len(split_mask):
                        continue
                    if split_mask[len(out)] != "_":
                        out += split_mask[len(out)]
                    out += chr(key)
                else:
                    out += chr(key)

        return out

    def collide(self, x, y):
        """Returns a widget that contains the point (x,y)"""

        for child in self.children:
            child: Widget
            if child.window.enclose(y, x):
                return child

        '''
        for child in self.children:
            child: Widget
            if child.bounds.collide(x, y):
                return child
        return None
        '''

    def swap_widget(self):
        directons = ""
        key = None
        sep = session_config.WindowPartition.separation
        preselected: Widget = self.focused
        preselected_color = session_config.ColorsConfig.alt_selected_pair

        while key not in [curses.KEY_ENTER, ord("\n")]:
            self.display_prompt("Move Mode | Move" + directons + " " * curses.COLS,
                                color=session_config.ColorsConfig.bright_select)
            key = self.window.getch()
            preselected.render_decorations()
            preselected.window.syncup()
            preselected_bounds = Bounds(preselected.window.getparyx()[0],
                                        preselected.window.getparyx()[1],
                                        preselected.window.getparyx()[0] + preselected.window.getmaxyx()[0],
                                        preselected.window.getparyx()[1] + preselected.window.getmaxyx()[1])
            match key:
                case 27:
                    break
                case curses.KEY_UP:
                    point = Point(preselected_bounds.center.x, preselected_bounds.top - sep - 1)
                    if 0 <= point.y <= curses.LINES:
                        preselected = self.collide(point.x, point.y)
                        directons += " UP"
                case curses.KEY_DOWN:
                    point = Point(preselected_bounds.center.x, preselected_bounds.bottom + sep + 1)
                    if 0 <= point.y <= curses.LINES:
                        preselected = self.collide(point.x, point.y)
                        directons += " DOWN"
                case curses.KEY_RIGHT:
                    point = Point(preselected_bounds.right + 1 + sep, preselected_bounds.center.y)
                    if 0 <= point.x <= curses.COLS:
                        preselected = self.collide(point.x, point.y)
                        directons += " RIGHT"
                case curses.KEY_LEFT:
                    point = Point(preselected_bounds.left - 1 - sep, preselected_bounds.center.y)
                    if 0 <= point.x <= curses.COLS:
                        preselected = self.collide(point.x, point.y)
                        directons += " LEFT"
            preselected.render_decorations(color=preselected_color)
            preselected.window.syncup()
            self.window.refresh()
        else:
            pres_ind = self.app.widgets.index(preselected)
            foc_ind = self.app.widgets.index(self.focused)

            self.app.widgets[pres_ind] = self.focused

            self.app.widgets[foc_ind] = preselected

            self.app.force_update_all()

    def open_new(self):
        overlay = OpenNewOverlay(self.window, self.app.all_widgets)

        key = None

        while key not in [ord("o"), 27]:
            self.app.draw_overlay(overlay)
            key = self.window.getch()
            if key == curses.KEY_UP:
                overlay.scroll(-1)
            if key == curses.KEY_DOWN:
                overlay.scroll(1)
            if key == ord("\n"):
                try:
                    self.app.add_widget(overlay.closed_widgets[overlay.selected_line])
                except IndexError:
                    pass
                break
