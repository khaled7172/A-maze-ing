"""Maze solver using recursive DFS.

Finds the path from entry to exit through the carved passages.
"""

from typing import List, Tuple

from maze.config import MazeConfig
from maze.maze_generator import DIRS


class MazeSolver:

    def __init__(self, maze: List[List[int]], config: MazeConfig) -> None:
        """Initialise solver with maze grid and config."""
        self.maze = maze
        self.config = config
        self.visited: List[List[bool]] = [
            [False] * config.width for _ in range(config.height)
        ]
        self.path: list[Tuple[int, int]] = []

    """
    Same DFS idea but with two differences:
    First it returns a bool now
    True means we found the exit
    False means dead end
    This checks if the wall is open before moving
    cell & wall returns non-zero if wall exists
    not (...) means wall is open, we can pass
    When it finds the exit it appends the cell and returns True
    all the way back up the cell stack, and each level appends itself to the
    path as it unwinds Thats why self.path.reverse() is needed in solve
    """

    def _dfs(self, x: int, y: int) -> bool:

        if (x, y) == self.config.exit:
            self.path.append((x, y))
            return True

        self.visited[y][x] = True

        for dx, dy, wall, _ in DIRS:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < self.config.width
                and 0 <= ny < self.config.height
                and not self.visited[ny][nx]
                and not (self.maze[y][x] & wall)  # wall bit set = wall exists
            ):
                if self._dfs(nx, ny):
                    self.path.append((x, y))
                    return True

        return False

    """
    Launches DFS from entry
    If no solution found raises an error
    Otherwise reverses the path, because cells were appended as DFS unwound
    so the path is backwards
    """

    def solve(self) -> List[Tuple[int, int]]:
        """Find and return the solution path from entry to exit.

        Returns:
            Ordered list of (x, y) cells from entry to exit.

        Raises:
            ValueError: If no path exists from entry to exit.
        """
        start_x, start_y = self.config.entry
        solved = self._dfs(start_x, start_y)

        if not solved:
            raise ValueError(
                f"No solution found from {
                    self.config.entry} to {
                    self.config.exit}")

        self.path.reverse()
        return self.path
