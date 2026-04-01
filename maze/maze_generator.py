"""
Maze generation module.
Supports four algorithms: DFS, PRIMS, ALDOUS, DIVISION.

Wall encoding (bitmask per cell):
    Bit 0 (1) = North
    Bit 1 (2) = East
    Bit 2 (4) = South
    Bit 3 (8) = West
A set bit means the wall is CLOSED (present).
Example North and west walls closed, else are open
that means:
north = 1
east = 0
south = 0
west = 1
Read as a binary number 1001(9 in decimal)
so the cell gets stored as just the number 9
one number represents 4 walls(bit masking)
1111 all bits on, all walls closed
when maze starts every cell is 15 all walls closed
Generator then knocks walls down to carve paths
To open a wall we use the &= and ~ oprators together
if we want to open the north wall of a cell all walls closed 1111
North = 1 = 0001
First we flip it with ~:
~NORTH = ~0001 = 1110
Then we AND it with the cell:
    1111(cells)
&   1110(North)
    ----
    1110
In code that looks like:
self.maze[y][x] &= ~NORTH
The north bit is now zero, and the wall is gone
Checking if a wall exists:
We use & to check
If we want to check if the north wall is closed
if cell & NORTH:
    #  wall is there
In binary:
    1110
&   0001
    ----
    0000 = 0 = False -> no wall

    1111
&   0001
    ----
    0001 = 1 = True -> wall exists
"""

import random
import sys
from typing import List

from maze.config import MazeConfig

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8

ALL_WALLS = 15

"""
This is a list of the 4 possible directions to move.
Each tuple has 4 values:
dx, dy how to move in the grid
the wall in the current cell
the wall on the neighbor cell
(0, -1, NORTH, SOUTH) means move up (y decreases)
and if we do, we open the north wall of the current cell
and the south wall of the neighbbor
"""
# (dx, dy, wall on current cell, opposite wall on neighbour)
DIRS = [
    (0, -1, NORTH, SOUTH),
    (1, 0, EAST, WEST),
    (0, 1, SOUTH, NORTH),
    (-1, 0, WEST, EAST),
]

# "42" pixel font — each digit is a list of (col, row) offsets
# rendered in a 3-wide x 5-tall grid per digit, gap of 1 col between digits
_DIGIT_4 = [
    (0, 0), (0, 1), (0, 2),
    (1, 2), (2, 2),
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
]
_DIGIT_2 = [
    (0, 0), (1, 0), (2, 0),
    (2, 1),
    (0, 2), (1, 2), (2, 2),
    (0, 3),
    (0, 4), (1, 4), (2, 4),
]

# Minimum maze size to fit the "42" pattern (2 digits * 3 wide + 1 gap + 2
# border)
_42_MIN_WIDTH = 10
_42_MIN_HEIGHT = 9


def _get_42_cells(offset_x: int, offset_y: int) -> list[tuple[int, int]]:
    """Return all (x,y) cell coords that form the '42' pattern.

    Args:
        offset_x: Left margin inside the maze.
        offset_y: Top margin inside the maze.

    Returns:
        List of (x, y) cell coordinates to be fully walled.
    """
    cells: list[tuple[int, int]] = []
    for col, row in _DIGIT_4:
        cells.append((offset_x + col, offset_y + row))
    for col, row in _DIGIT_2:
        # 4 = digit width + gap
        cells.append((offset_x + 4 + col, offset_y + row))
    return cells


class MazeGenerator:
    """Generate a maze using one of four algorithms.

    Supported algorithms: DFS, PRIMS, ALDOUS, DIVISION.

    Args:
        config: A MazeConfig instance with all generation parameters.

    Example::

        from maze.config import MazeConfig
        from maze.maze_generator import MazeGenerator

        cfg = MazeConfig(
            width=20, height=20,
            entry=(0, 0), exit=(19, 19),
            perfect=True, output_file="maze.txt", seed=42,
            algorithm="ALDOUS")
        gen = MazeGenerator(cfg)
        maze = gen.generate()   # List[List[int]] — bitmask per cell
        gen.save_hex()          # writes output file
    """

    def __init__(self, config: MazeConfig) -> None:
        """Initialise generator with a MazeConfig."""
        self.config = config
        self.visited: List[List[bool]] = [
            [False] * config.width for _ in range(config.height)
        ]
        """
        random.Random() creates a private random number generator
        its locked to the seed
        will always produce the same sequence of random numbers
        same seed, same maze everytime
        """
        self.rand = random.Random(config.seed)
        self.maze: List[List[int]] = self._init_empty_maze()
        self._42_cells: list[tuple[int, int]] = []
        self._42_cells_set: set[tuple[int, int]] = set()

    """
    This creates the maze grid, Every cells starts at ALL_WALLS which is 15
    all walls closed
    """

    def _init_empty_maze(self) -> List[List[int]]:
        """Return a grid where every cell has all four walls closed."""
        return [
            [ALL_WALLS for _ in range(self.config.width)]
            for _ in range(self.config.height)
        ]

    def _open_walls(
            self,
            x: int,
            y: int,
            nx: int,
            ny: int,
            wall_here: int,
            wall_there: int) -> None:
        """Remove the shared wall between (x,y) and (nx,ny).

        Args:
            x, y: Current cell coordinates.
            nx, ny: Neighbour cell coordinates.
            wall_here: Wall bit to clear on the current cell.
            wall_there: Wall bit to clear on the neighbour cell.
        """
        self.maze[y][x] &= ~wall_here
        self.maze[ny][nx] &= ~wall_there

    def _dfs(self, x: int, y: int) -> None:
        """Recursively carve passages via DFS backtracker.

        Args:
            x: Starting cell x coordinate.
            y: Starting cell y coordinate.
        """
        """
        First we mark the current cell visited so we dont come back to it
        second we copy the DIRS list, The [:] is important, without it
        shuffling would modify the original DIRS list permanently
        we want a fresh copy each time
        last we randomly shuffle the 4 directions, making the maze random
        we try directions in a different order every time
        """
        self.visited[y][x] = True
        directions = DIRS[:]
        self.rand.shuffle(directions)
        """
        We loop through the shuffled directions
        for each direction we calculate the neighbor's coordinates by adding
        the direction offset to the current position
        then we check 4 conditions before moving:
        if neighbor in within horizontal and vertical bounds
        if neighbor hasn't been visited yet
        if it has skip it
        if neighbor isn't a "42" cell
        if all 4 conditions pass:
        knock down the wall between current cell and neighbor
        jump into neighbor and repeat the whole process from there
        """
        for dx, dy, wall_here, wall_there in directions:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < self.config.width
                and 0 <= ny < self.config.height
                and not self.visited[ny][nx]
                and (nx, ny) not in self._42_cells_set
            ):
                self._open_walls(x, y, nx, ny, wall_here, wall_there)
                self._dfs(nx, ny)

    def _embed_42(self) -> None:
        """Mark cells forming '42' as visited so DFS skips them.

        Prints a warning if the maze is too small to fit the pattern.
        """
        w, h = self.config.width, self.config.height
        if w < _42_MIN_WIDTH or h < _42_MIN_HEIGHT:
            print(f"Maze ({w}x{h}) too small for '42' pattern.")
            sys.exit(1)

        # Center the pattern
        pattern_w = 7  # 7 cells wide (3 for "4", 1 gap, 3 for "2")
        pattern_h = 5  # 5 cells tall
        offset_x = (w - pattern_w) // 2
        offset_y = (h - pattern_h) // 2

        self._42_cells = _get_42_cells(offset_x, offset_y)
        self._42_cells_set = set(self._42_cells)
        for cx, cy in self._42_cells:
            self.visited[cy][cx] = True  # DFS will never enter these cells

    def generate(self) -> List[List[int]]:
        """Generate and return the maze grid.

        Returns:
            2-D list of ints — each int is a 4-bit wall bitmask.
        """
        self._embed_42()
        x, y = self.config.entry
        if self.config.algorithm == "PRIMS":
            self._prims(x, y)
        elif self.config.algorithm == "ALDOUS":
            self._aldous_broder()
        elif self.config.algorithm == "DIVISION":
            self._recursive_division()
        elif self.config.algorithm == "WILSON":
            self._wilson()
        elif self.config.algorithm == "BINARYTREE":
            self._binary_tree()
        else:
            self._dfs(x, y)
        if not self.config.perfect:
            self._add_loops()
        return self.maze

    def _prims(self, x: int, y: int) -> None:
        """Generate maze using Prim's algorithm.

        Args:
            x: Starting cell x coordinate.
            y: Starting cell y coordinate.
        """
        self.visited[y][x] = True
        frontiers = []

        for dx, dy, wall_here, wall_there in DIRS:
            nx, ny = x + dx, y + dy
            if (
                0 <= nx < self.config.width
                and 0 <= ny < self.config.height
                and not self.visited[ny][nx]
                and (nx, ny) not in self._42_cells_set
            ):
                frontiers.append((nx, ny, x, y, wall_there, wall_here))

        while frontiers:
            idx = self.rand.randint(0, len(frontiers) - 1)
            nx, ny, px, py, wall_here, wall_there = frontiers.pop(idx)

            if self.visited[ny][nx]:
                continue

            self._open_walls(px, py, nx, ny, wall_there, wall_here)
            self.visited[ny][nx] = True

            for dx, dy, wh, wt in DIRS:
                nnx, nny = nx + dx, ny + dy
                if (
                    0 <= nnx < self.config.width
                    and 0 <= nny < self.config.height
                    and not self.visited[nny][nnx]
                    and (nnx, nny) not in self._42_cells_set
                ):
                    frontiers.append((nnx, nny, nx, ny, wt, wh))

    def _aldous_broder(self) -> None:
        """Generate a perfect maze using the Aldous-Broder algorithm.

        Performs a random walk across the grid. The first time a cell is
        visited, carve the wall from the previous cell to it. Continue
        until every non-42 cell has been visited.
        """
        w, h = self.config.width, self.config.height

        # Count how many cells need to be visited (exclude 42 cells)
        total = w * h - len(self._42_cells_set)

        # Pick a random starting cell that is not a 42 cell
        while True:
            x = self.rand.randint(0, w - 1)
            y = self.rand.randint(0, h - 1)
            if (x, y) not in self._42_cells_set:
                break

        self.visited[y][x] = True
        visited_count = 1

        while visited_count < total:
            # Pick a random neighbour (any, not just unvisited)
            directions = DIRS[:]
            self.rand.shuffle(directions)

            for dx, dy, wall_here, wall_there in directions:
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < w
                    and 0 <= ny < h
                    and (nx, ny) not in self._42_cells_set
                ):
                    if not self.visited[ny][nx]:
                        # First time visiting this neighbour — carve the wall
                        self._open_walls(x, y, nx, ny, wall_here, wall_there)
                        self.visited[ny][nx] = True
                        visited_count += 1
                    # Move to the neighbour regardless of
                    # whether it was visited
                    x, y = nx, ny
                    break

    def _recursive_division(self) -> None:
        """Generate a maze using recursive division.

        Unlike DFS and Prim's, this algorithm starts with a fully OPEN grid
        and adds walls. It splits a region in half with a wall, leaves one
        gap in it, then recursively does the same to each half.
        """
        w, h = self.config.width, self.config.height

        # Start with all interior walls open — clear all wall bits except
        # the outer border
        for y in range(h):
            for x in range(w):
                walls = 0
                if y == 0:
                    walls |= NORTH
                if x == w - 1:
                    walls |= EAST
                if y == h - 1:
                    walls |= SOUTH
                if x == 0:
                    walls |= WEST
                self.maze[y][x] = walls

        # Recursively divide the full grid
        self._divide(0, 0, w, h)

    def _divide(
            self,
            x: int,
            y: int,
            width: int,
            height: int) -> None:
        """Recursively divide a region by adding a wall with one passage.

        Args:
            x: Left edge of the region.
            y: Top edge of the region.
            width: Width of the region in cells.
            height: Height of the region in cells.
        """
        # Base case: region is too small to divide
        if width < 2 or height < 2:
            return

        # Choose direction: divide horizontally or vertically
        # Bias toward dividing the longer axis for more balanced mazes
        if width > height:
            horizontal = False
        elif height > width:
            horizontal = True
        else:
            horizontal = self.rand.randint(0, 1) == 0

        if horizontal:
            # Draw a horizontal wall somewhere inside the region
            # wall_y is the row just below which we place the wall
            wall_y = y + self.rand.randint(1, height - 1)
            # Pick one random gap cell — the passage through the wall
            gap_x = x + self.rand.randint(0, width - 1)

            for cx in range(x, x + width):
                if cx == gap_x:
                    continue
                # Skip 42 cells — don't add walls through them
                if (cx, wall_y - 1) in self._42_cells_set:
                    continue
                if (cx, wall_y) in self._42_cells_set:
                    continue
                # Add south wall to the cell above and north wall to cell below
                self.maze[wall_y - 1][cx] |= SOUTH
                self.maze[wall_y][cx] |= NORTH

            # Recurse into the two halves
            self._divide(x, y, width, wall_y - y)
            self._divide(x, wall_y, width, y + height - wall_y)

        else:
            # Draw a vertical wall somewhere inside the region
            wall_x = x + self.rand.randint(1, width - 1)
            gap_y = y + self.rand.randint(0, height - 1)

            for cy in range(y, y + height):
                if cy == gap_y:
                    continue
                if (wall_x - 1, cy) in self._42_cells_set:
                    continue
                if (wall_x, cy) in self._42_cells_set:
                    continue
                # Add east wall to the cell on the left and west to the right
                self.maze[cy][wall_x - 1] |= EAST
                self.maze[cy][wall_x] |= WEST

            # Recurse into the two halves
            self._divide(x, y, wall_x - x, height)
            self._divide(wall_x, y, x + width - wall_x, height)

    def _wilson(self) -> None:
        """Generate a perfect maze using Wilson's algorithm (loop-erased walk).

        Pick any unvisited cell and do a random walk until a visited cell is
        reached. If the walk loops back on itself, erase the loop. Once a
        visited cell is reached, carve the entire recorded path into the maze.
        Repeat until every non-42 cell is visited.
        """
        w, h = self.config.width, self.config.height

        # Mark the entry cell as the first visited cell to seed the algorithm
        sx, sy = self.config.entry
        self.visited[sy][sx] = True

        # Build a list of all unvisited non-42 cells
        unvisited: list[tuple[int, int]] = [
            (x, y)
            for y in range(h)
            for x in range(w)
            if not self.visited[y][x]
            and (x, y) not in self._42_cells_set
        ]

        while unvisited:
            # Pick a random unvisited cell to start a walk from
            start = unvisited[self.rand.randint(0, len(unvisited) - 1)]

            # path stores the walk order, came_from maps each cell to how we
            # arrived at it so we know which wall to carve
            walk: list[tuple[int, int]] = [start]
            came_from: dict[
                tuple[int, int],
                tuple[int, int, int, int]
            ] = {}

            cx, cy = start

            while not self.visited[cy][cx]:
                directions = DIRS[:]
                self.rand.shuffle(directions)

                for dx, dy, wall_here, wall_there in directions:
                    nx, ny = cx + dx, cy + dy
                    if (
                        0 <= nx < w
                        and 0 <= ny < h
                        and (nx, ny) not in self._42_cells_set
                    ):
                        came_from[(nx, ny)] = (cx, cy, wall_here, wall_there)

                        if (nx, ny) in walk:
                            # Loop detected — erase everything after loop start
                            loop_start = walk.index((nx, ny))
                            for cell in walk[loop_start + 1:]:
                                came_from.pop(cell, None)
                            walk = walk[:loop_start + 1]
                        else:
                            walk.append((nx, ny))

                        cx, cy = nx, ny
                        break

            # Walk reached a visited cell — carve the whole path
            for cell in walk:
                if cell in came_from:
                    px, py, wall_here, wall_there = came_from[cell]
                    self._open_walls(
                        px, py, cell[0], cell[1], wall_here, wall_there
                    )
                self.visited[cell[1]][cell[0]] = True

            # Rebuild unvisited list
            unvisited = [
                (x, y)
                for y in range(h)
                for x in range(w)
                if not self.visited[y][x]
                and (x, y) not in self._42_cells_set
            ]

    def _binary_tree(self) -> None:
        """Generate a maze using the Binary Tree algorithm.

        For every cell, randomly carve either north or east. If north is out
        of bounds, carve east. If east is out of bounds, carve north. The
        top-right corner has nowhere to go so it stays walled on those sides.
        Produces mazes with a strong diagonal bias toward the top-right corner.
        """
        w, h = self.config.width, self.config.height

        for y in range(h):
            for x in range(w):
                if (x, y) in self._42_cells_set:
                    continue

                can_north = y > 0 and (x, y - 1) not in self._42_cells_set
                can_east = (
                    x < w - 1 and (x + 1, y) not in self._42_cells_set
                )

                if can_north and can_east:
                    if self.rand.randint(0, 1) == 0:
                        self._open_walls(x, y, x, y - 1, NORTH, SOUTH)
                    else:
                        self._open_walls(x, y, x + 1, y, EAST, WEST)
                elif can_north:
                    self._open_walls(x, y, x, y - 1, NORTH, SOUTH)
                elif can_east:
                    self._open_walls(x, y, x + 1, y, EAST, WEST)

    def _add_loops(self) -> None:
        """Remove random interior walls to create loops for imperfect maze."""
        w, h = self.config.width, self.config.height
        extra = (w * h) // 10  # remove ~10% extra walls

        for _ in range(extra):
            if self.rand.randint(0, 1) == 0:
                # punch horizontal wall (EAST/WEST)
                x = self.rand.randint(0, w - 2)
                y = self.rand.randint(0, h - 1)
                if (x, y) in self._42_cells_set:
                    continue
                if (x + 1, y) in self._42_cells_set:
                    continue
                self._open_walls(x, y, x + 1, y, EAST, WEST)
            else:
                # punch vertical wall (SOUTH/NORTH)
                x = self.rand.randint(0, w - 1)
                y = self.rand.randint(0, h - 2)
                if (x, y) in self._42_cells_set:
                    continue
                if (x, y + 1) in self._42_cells_set:
                    continue
                self._open_walls(x, y, x, y + 1, SOUTH, NORTH)

    """
    This writes the maze to a file
    format(cell, "X") converts the cell's number to uppercase hex
    so 15 becomes "F", 9 becomes "9"
    """

    def save_hex(
            self, solution_path: list[tuple[int, int]] | None = None) -> None:
        """Write the maze grid and optional solution path to the output file.

        Args:
            solution_path: Optional list of (x, y) cells from entry to exit.
        """
        path = self.config.output_file
        with open(path, "w") as f:
            for row in self.maze:
                f.write("".join(format(cell, "X") for cell in row) + "\n")

            if solution_path:
                ex, ey = self.config.entry
                ox, oy = self.config.exit
                directions = _path_to_directions(solution_path)
                f.write("\n")
                f.write(f"{ex},{ey}\n")
                f.write(f"{ox},{oy}\n")
                f.write("".join(directions) + "\n")


"""
This converts a list of coordinates into a list of direction letters
It loops through the path, looking at each pair of consecutive calls
for each pair it calculates dx and dy, and the difference between them
then based on the difference it appends the correct letter
"""


def _path_to_directions(path: list[tuple[int, int]]) -> list[str]:
    """Convert a list of (x, y) coordinates into direction letters.

    Args:
        path: Ordered list of (x, y) cells.

    Returns:
        List of direction characters: N, E, S, or W.
    """
    dirs: list[str] = []
    for i in range(len(path) - 1):
        x0, y0 = path[i]
        x1, y1 = path[i + 1]
        dx, dy = x1 - x0, y1 - y0
        if dx == 1:
            dirs.append("E")
        elif dx == -1:
            dirs.append("W")
        elif dy == -1:
            dirs.append("N")
        elif dy == 1:
            dirs.append("S")
    return dirs
