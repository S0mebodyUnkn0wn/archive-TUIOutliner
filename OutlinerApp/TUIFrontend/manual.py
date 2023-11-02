import curses


class HelpPage:

    @staticmethod
    def render(window: curses.window):
        help_message: str = '''
        keys:
            Tab - switch focus between widgets
            f - toggle fullscreen for focused widget
            s - open split view
            ? - show this help page
            
            shift+w - close focused widget
            shift+ArrowKeys - resize widgets
            shift+r - rest view
            
            h - hide/unhide done tasks (globally)
            t - toggle deadlines in event calendar 
            T - show today
                       
            a - add a new task/event
            r - delete a task/event
        '''
        y = 2
        x = 2
        for line in help_message.splitlines():
            window.addnstr(y, x, line, curses.COLS)
            y += 1
