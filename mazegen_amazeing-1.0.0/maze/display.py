"""Terminal ASCII display for the maze.

Renders the maze using box-drawing characters with ANSI colour support.
Supports interactive mode: re-generate, toggle solution path, change colours.
"""

import os
import sys
import termios
import tty
from typing import List, Tuple, Callable

from maze.config import MazeConfig
from maze.maze_generator import NORTH, EAST, SOUTH, WEST

# ── ANSI colour codes ───────────────────────────────────────────────────
"""
\033[ is the escape sequence that starts a colour command
"""
RESET = "\033[0m"
BOLD = "\033[1m"

COLOURS = {
    "white": "\033[97m",
    "cyan": "\033[96m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "magenta": "\033[95m",
    "blue": "\033[94m",
    "red": "\033[91m",
}

COLOUR_NAMES = list(COLOURS.keys())

PATH_COLOUR = "\033[92m"    # green for solution dots
ENTRY_COLOUR = "\033[93m"   # yellow for S
EXIT_COLOUR = "\033[91m"    # red for E
_42_COLOUR = "\033[35m"     # magenta for 42 cells

# ── Box-drawing characters ──────────────────────────────────────────────

WALL_H = "───"   # horizontal wall segment (3 chars wide to match cell)
WALL_V = "│"
CORNER = "+"
SPACE = "   "    # open horizontal
HALF_OPEN = " "  # open vertical

CELL_W = 3        # printable chars per cell horizontally
CELL_H = 1        # printable rows per cell (between h-walls)

"""
os.name == "nt" means Windows, so it uses cls
On Mac/linux it uses clear
"""


def _clear() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


"""
This reads a single keypress without waiting for Enter
sys.stdin.fileno() gets the file descriptor of the terminal input
termios.tcgetattr(fd) saves the current terminal settings so we can restore
them later
tty.setraw(fd) switches terminal to raw mode where every keypress
is immediatly available
sys.stdin.read(1) reads exactly one character
termios.tcsetattr(fd, termios.TCSADRAIN, old) restore the original terminal
settings in the finally block, so even ig something crashes the terminal
isn't left in raw mode
"""


def _getch() -> str:
    """Read a single keypress without waiting for Enter (Unix only).

    Returns:
        The pressed character.
    """
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


"""
This function decides what to draw inside a cell, 3 characters
It takes the cell coordinates, the config, the solution path,
whether to show the path, and the "42" cells
First check if the cell is entry or exit
Entry shows a yellow bold S
exit shows a red bold E
if its a 42 cell fill it with magenta
if path is visible and this cell is on it
show a green dot
otherwise return a space
"""


def _cell_content(
    x: int, y: int,
    config: MazeConfig,
    path_set: set[Tuple[int, int]],
    show_path: bool,
    cells_42: set[Tuple[int, int]],
) -> str:
    """Return the 3-char string drawn inside a cell.

    Args:
        x, y: Cell coordinates.
        config: Maze config (for entry/exit positions).
        path_set: Set of solution path coordinates.
        show_path: Whether the solution is currently visible.
        cells_42: Set of coordinates forming the '42' pattern.

    Returns:
        A 3-character coloured string.
    """
    ex, ey = config.entry
    ox, oy = config.exit

    if (x, y) == (ex, ey):
        return f"{ENTRY_COLOUR}{BOLD} S {RESET}"
    if (x, y) == (ox, oy):
        return f"{EXIT_COLOUR}{BOLD} E {RESET}"
    if (x, y) in cells_42:
        return f"{_42_COLOUR}░░░{RESET}"
    if show_path and (x, y) in path_set:
        return f"{PATH_COLOUR} · {RESET}"
    return SPACE


def render(
    maze: List[List[int]],
    config: MazeConfig,
    solution: List[Tuple[int, int]],
    show_path: bool,
    wall_colour_name: str,
    cells_42: set[Tuple[int, int]],
) -> None:
    """Print the full maze to stdout.

    Args:
        maze: 2-D bitmask grid.
        config: Maze config.
        solution: Solved path as list of (x,y).
        show_path: Whether to overlay the solution.
        wall_colour_name: Key into COLOURS dict.
        cells_42: Coordinates of '42' pattern cells.
    """
    wc = COLOURS.get(wall_colour_name, COLOURS["white"])
    h, w = config.height, config.width
    path_set: set[Tuple[int, int]] = set(solution)

    lines: list[str] = []

    for y in range(h):
        # ── Top border row for this maze row ─────────────────────────────────
        top = ""
        for x in range(w):
            cell = maze[y][x]
            top += wc + CORNER + RESET
            top += (wc + WALL_H + RESET) if (cell & NORTH) else SPACE
        top += wc + CORNER + RESET
        lines.append(top)

        # ── Cell row ─────────────────────────────────────────────────────────
        mid = ""
        for x in range(w):
            cell = maze[y][x]
            mid += (wc + WALL_V + RESET) if (cell & WEST) else HALF_OPEN
            mid += _cell_content(x, y, config, path_set, show_path, cells_42)
        # rightmost wall
        cell = maze[y][w - 1]
        mid += (wc + WALL_V + RESET) if (cell & EAST) else HALF_OPEN
        lines.append(mid)

    # ── Bottom border ───────────────────────────────────────────────────────
    bot = ""
    for x in range(w):
        cell = maze[h - 1][x]
        bot += wc + CORNER + RESET
        bot += (wc + WALL_H + RESET) if (cell & SOUTH) else SPACE
    bot += wc + CORNER + RESET
    lines.append(bot)

    print("\n".join(lines))


def _print_controls(show_path: bool, colour: str) -> None:
    """Print the interactive control bar below the maze.

    Args:
        show_path: Current path visibility state.
        colour: Current wall colour name.
    """
    path_label = "Hide path" if show_path else "Show path"
    print(
        f"\n  {BOLD}[r]{RESET} Re-generate  "
        f"{BOLD}[p]{RESET} {path_label}  "
        f"{BOLD}[c]{RESET} Wall colour ({colour})  "
        f"{BOLD}[q]{RESET} Quit"
    )


def interactive(
    # callable(seed) -> (maze, solution, cells_42)
    maze_factory: Callable[[int], tuple[List[List[int]], List[Tuple[int, int]],
                                        set[tuple[int, int]]]],
    config: MazeConfig,
    initial_maze: List[List[int]],
    initial_solution: List[Tuple[int, int]],
    initial_42: set[Tuple[int, int]],
) -> None:

    maze = initial_maze
    solution = initial_solution
    cells_42 = initial_42
    show_path = False
    colour_idx = 0
    seed_counter = 0 if config.seed is None else config.seed

    while True:
        _clear()
        colour_name = COLOUR_NAMES[colour_idx % len(COLOUR_NAMES)]
        render(maze, config, solution, show_path, colour_name, cells_42)
        _print_controls(show_path, colour_name)

        try:
            key = _getch().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if key == 'q':
            print("\nBye!")
            break
        elif key == 'p':
            show_path = not show_path
        elif key == 'c':
            colour_idx += 1
        elif key == 'r':
            seed_counter += 1
            maze, solution, cells_42 = maze_factory(seed_counter)
