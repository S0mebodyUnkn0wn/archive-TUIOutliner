import curses
import sys

import OutlinerApp.TUIFrontend.application
import OutlinerApp.TextualFronted.application
if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=="--textual":
        OutlinerApp.TextualFronted.application.SuperOutliner().run()
    else:
        curses.wrapper(OutlinerApp.TUIFrontend.application.Application)
