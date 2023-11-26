from textual.app import App, ComposeResult
from textual.layouts.grid import GridLayout
from textual.widgets import Welcome, Footer

from .widgets import TaskOutliner, CalendarOutliner


class SuperOutliner(App):
    CSS_PATH = "application.tcss"

    def compose(self) -> ComposeResult:
        yield CalendarOutliner()
        yield TaskOutliner()

        yield Footer()


if __name__ =="__main__":
    print("starting")
    app = SuperOutliner()
    app.run()