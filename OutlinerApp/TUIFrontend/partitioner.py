import curses

from .widgets import Widget
from ..Backend.configs import session_config
from .data import Bounds


def _get_open(widgets: list[Widget]):
    open_widgets = []
    for widget in widgets:
        if widget.is_open:
            open_widgets.append(widget)
    return open_widgets


def partition_grid(widgets: list[Widget]):
    window_length = curses.LINES
    window_width = curses.COLS

    open_widgets = _get_open(widgets)
    layout = []
    grid_cols = 1
    grid_rows = 1
    while grid_rows * grid_cols < len(open_widgets):
        if grid_cols < grid_rows:
            grid_cols += 1
        else:
            grid_rows += 1

    grid_cell_length = window_length // grid_rows
    grid_cell_width = window_width // grid_cols
    grid_sep = session_config.WindowPartition.separation
    for col in range(grid_cols - 1, -1, -1):
        for row in range(grid_rows - 1, -1, -1):
            cell_top = row * grid_cell_length
            cell_left = col * grid_cell_width
            cell_bottom = cell_top + grid_cell_length - grid_sep // 2 if row < grid_rows - 1 else curses.LINES
            cell_right = cell_left + grid_cell_width - grid_sep if col < grid_cols - 1 else curses.COLS
            cell_bounds = Bounds(cell_top, cell_left, cell_bottom, cell_right)
            layout.append(cell_bounds)

    return layout


def partition_halves(widgets: list[Widget]):
    layout = [Bounds(0, 0, curses.LINES, curses.COLS)]
    open_widgets = _get_open(widgets)
    sep = session_config.WindowPartition.separation

    while len(layout) < len(open_widgets):
        prev = layout[-1]
        nxt = Bounds()
        nxt.left = prev.left
        nxt.bottom = prev.bottom
        if len(layout) % 2:
            nxt.right = nxt.left + (prev.right-prev.left) * 3 // 5 + session_config.WindowPartition.horizontal
            nxt.top = prev.top
            prev.left = nxt.right + sep
        else:
            nxt.top = nxt.bottom - (prev.bottom-prev.top) * 2 // 5 + session_config.WindowPartition.vertical
            nxt.right = prev.right
            prev.bottom = nxt.top - sep // 2

        layout.append(nxt)

    return layout


def partition_space(widgets: list[Widget], mode: str = "auto"):
    """Available modes: auto, halves, grid """

    # Note that the layout is read in reverse (right to left, bottom to top)
    match mode.lower():
        case "auto":
            return partition_halves(widgets)
        case "halves":
            return partition_halves(widgets)
        case "grid":
            return partition_grid(widgets)
