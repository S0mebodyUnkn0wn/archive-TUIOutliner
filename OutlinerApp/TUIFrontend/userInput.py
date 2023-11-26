import curses
from typing import List

import watchdog
from watchdog.events import FileSystemEventHandler

from . import application, widgets
from . import manual
from .data import Bounds, Point
from .outliners import TaskOutliner, CalendarOutliner, Outliner
from .overlays import SelectorOverlay
from .widgets import Widget, Header
from ..Backend.configs import session_config


class InputManager(FileSystemEventHandler):

    def on_modified(self, event):
        event: watchdog.events.FileSystemEvent
        self.app.update_data_all()

    def __init__(self, app, window):
        self.focused: Widget = None
        self.app: application.Application = app
        self.window: curses.window = window

    def handle_input(self):
        key = self.window.getch()

        if key == curses.KEY_RESIZE:
            curses.resize_term(*self.window.getmaxyx())
            self.app.enqueue_partition_update()
            return

        for child in self.app.widgets:
            if child.is_focused:
                self.focused = child
                break
        else:
            self.focused: Widget = self.app.widgets[0]
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
        if isinstance(self.focused, Outliner):
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
            if key == ord("e"):
                self.focused.edit_entry()
                return
            if key == ord("a"):
                self.focused.add_entry()
                return

            if key == ord("r"):
                self.focused.remove_entry()
                return

        if isinstance(self.focused, TaskOutliner):
            if key == ord("s"):
                self.focused.create_subtask()
                return
            if key == ord("h"):
                self.focused.toggle_hide_done()
                return

            if key == ord("d"):
                self.focused.mark_done()
                return

        elif isinstance(self.focused, CalendarOutliner):
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

        if key == ord("O"):
            self.open_new(replace_focused=True)
            return

        if key == ord("W"):
            self.close_focused()
            return

        if key == ord("f"):
            # self.fullscreen()
            return

        if key == ord("\t"):
            self.move_focus(False)
            return
        if key == 353:  # If shift+tab
            self.move_focus(True)
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

    def show_help(self):
        self.window.clear()
        manual.HelpPage.render(self.window)
        self.window.getch()

    def move_focus(self, reverse=False):
        if len(self.app.widgets) == 1:
            return
        d = -1 if reverse else 1
        foc_ind = self.app.widgets.index(self.focused)
        self.focused.unfocus()
        self.focused = self.app.widgets[(foc_ind - d) % len(self.app.widgets)].focus()

    def close_focused(self):
        if len(self.app.widgets) == 1:
            return
        self.focused: Widget
        widget_to_colose = self.focused
        self.move_focus(False)
        self.app.widgets.remove(widget_to_colose)

    def reset_partition(self):
        session_config.WindowPartition.horizontal = 0
        session_config.WindowPartition.vertical = 0

    def partition_down(self):
        for child in self.app.widgets:
            if child.is_focused:
                session_config.WindowPartition.vertical += 1

    def partition_up(self):
        for child in self.app.widgets:
            if child.is_focused:
                session_config.WindowPartition.vertical -= 1

    def partition_left(self):
        session_config.WindowPartition.horizontal -= 1

    def partition_right(self):
        session_config.WindowPartition.horizontal += 1

    def collide(self, x, y):
        """Returns a widget that contains the point (x,y)"""

        for child in self.app.widgets:
            child: Widget
            if child.window.enclose(y, x):
                return child

    def display_prompt(self, prompt: str, color=session_config.ColorsConfig.generic_text_pair):
        try:
            self.window.addnstr(curses.LINES - 1, 0, prompt, curses.COLS, curses.color_pair(color))
        except curses.error:
            pass

    # Input States defined below

    def recieve_text(self, prompt: str, split_mask=None, start_with: str = "") -> str:
        out = start_with
        cursor = ""
        curses.curs_set(1)
        cursor_pos = len(start_with)
        key = None
        while key not in [ord("\n"), curses.KEY_ENTER]:
            self.display_prompt(cursor + " " * curses.COLS)
            self.display_prompt(f"{prompt}{out[:cursor_pos]}{cursor}{out[cursor_pos:]}")
            self.window.move(curses.LINES-1,len(prompt)+cursor_pos)
            key = self.window.getch()
            if key == curses.KEY_END:
                cursor_pos = len(out)
            if key == curses.KEY_HOME:
                cursor_pos = 0
            if key == 567: # CTRL + RIGHT
                next_word = out.find(" ",cursor_pos+1)
                if next_word!=-1:
                    cursor_pos = next_word
                else:
                    cursor_pos = len(out)
            if key == 552: # CTRL + LEFT
                prev_word = out.rfind(" ", 0, cursor_pos)
                if prev_word != -1:
                    cursor_pos = prev_word
                else:
                    cursor_pos = 0
            if key == curses.KEY_DC:
                out = out[:cursor_pos]+out[cursor_pos+1:]
                continue
            if key == curses.KEY_BACKSPACE and cursor_pos>0:
                out = out[:cursor_pos-1]+out[cursor_pos:]
                cursor_pos -= 1
                continue
            if key == curses.KEY_EXIT or key == 27:
                return ""
            if key == curses.KEY_LEFT and cursor_pos > 0:
                cursor_pos-=1
                continue
            if key == curses.KEY_RIGHT and cursor_pos<len(out):
                cursor_pos+=1
                continue
            if 32 <= key <= 255:
                if split_mask is not None:
                    if len(out) + 1 > len(split_mask):
                        continue
                    if split_mask[len(out)] != "_":
                        out += split_mask[len(out)]
                        cursor_pos += 1
                out = out[:cursor_pos] + chr(key) + out[cursor_pos:]
                cursor_pos += 1
                continue
        curses.curs_set(0)

        return out

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
        else:
            try:
                pres_ind = self.app.widgets.index(preselected)
            except ValueError:
                raise ValueError(preselected, self.app.widgets)
            foc_ind = self.app.widgets.index(self.focused)

            self.app.widgets[pres_ind] = self.focused
            self.app.widgets[pres_ind] = self.focused

            self.app.widgets[foc_ind] = preselected
            self.app.widgets[foc_ind] = preselected

            self.app.force_update_all()

    def open_new(self,replace_focused = False):
        if replace_focused:
            header = Header("Replace Focused Widget With:", align="center")
        else:
            header = Header("Open New Widget", align="center")

        overlay = SelectorOverlay(self.window, self.app, self.app.all_widgets,header)

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
                    new_widget_class = overlay.items[overlay.selected_line]
                    if replace_focused:
                        new_widget: Widget = new_widget_class(self.focused.window,self.app)
                        self.app.widgets[self.app.widgets.index(self.focused)] = new_widget
                        self.focused = new_widget.focus()
                    else:
                        self.app.add_widget(new_widget_class).focus()
                        self.focused.unfocus()
                        self.focused = new_widget_class
                except IndexError:
                    pass
                break
