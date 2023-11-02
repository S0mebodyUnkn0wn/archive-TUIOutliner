import curses
import OutlinerApp.TUIFrontend.application

if __name__ == '__main__':
    curses.wrapper(OutlinerApp.TUIFrontend.application.Application)
