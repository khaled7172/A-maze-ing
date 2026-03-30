"""Maze solver using BFS.

Finds the shortest path from entry to exit through the carved passages.
"""

from collections import deque
from typing import List, Tuple

from maze.config import MazeConfig
from maze.maze_generator import DIRS


class MazeSolver:

    def __init__(self, maze: List[List[int]], config: MazeConfig) -> None:
        """Initialise solver with maze grid and config."""
        self.maze = maze
        self.config = config

    def solve(self) -> List[Tuple[int, int]]:
        """Find and return the shortest solution path from entry to exit.

        Uses BFS so the first time the exit is reached, it is guaranteed
        to be via the fewest steps.

        Returns:
            Ordered list of (x, y) cells from entry to exit.

        Raises:
            ValueError: If no path exists from entry to exit.
        """
        start = self.config.entry
        end = self.config.exit

        # Each queue item is a path so far (list of coords).
        # We start with a path containing only the entry cell.
        queue: deque[list[Tuple[int, int]]] = deque()
        queue.append([start])

        visited: set[Tuple[int, int]] = {start}

        while queue:
            path = queue.popleft()
            x, y = path[-1]  # current cell is the last one in the path

            if (x, y) == end:
                return path

            for dx, dy, wall, _ in DIRS:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < self.config.width
                    and 0 <= ny < self.config.height
                    and (nx, ny) not in visited
                    and not (self.maze[y][x] & wall)  # wall is open
                ):
                    visited.add((nx, ny))
                    queue.append(path + [(nx, ny)])

        raise ValueError(
            f"No solution found from {self.config.entry} to {self.config.exit}"
        )
