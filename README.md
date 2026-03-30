*This project has been created as part of the 42 curriculum by mkhanji, khhammou*

---

## Description

A-Maze-ing is a configurable maze generator, solver, and interactive terminal visualiser written in Python 3.10+.

It generates mazes using either the **recursive DFS backtracker** or **Prim's algorithm**, both of which produce *perfect mazes* — mazes with exactly one path between any two cells, equivalent to a spanning tree of the cell graph. The maze is solved with a BFS pass guaranteeing the shortest path, which is stored in the output file alongside the hex-encoded maze structure.

The terminal display renders walls using Unicode box-drawing characters with full ANSI colour support and supports interactive re-generation, path toggling, and colour cycling.

---

## Instructions

### Requirements
- Python 3.10 or later
- No external runtime dependencies (standard library only)

### Run

```bash
make run
# or directly:
python3 a_maze_ing.py config.txt
```

### Interactive controls

| Key | Action |
|-----|--------|
| `p` | Show / hide solution path |
| `r` | Re-generate a new maze |
| `c` | Cycle wall colour |
| `q` | Quit |

### Debug

```bash
make debug
```

### Lint

```bash
make lint
```

### Build pip package

```bash
make build
# produces dist/mazegen_amazeing-1.0.0-*.whl and .tar.gz
```

---

## Configuration file format

One `KEY=VALUE` pair per line. Lines starting with `#` are comments.

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `WIDTH` | int | Maze width in cells | `WIDTH=40` |
| `HEIGHT` | int | Maze height in cells | `HEIGHT=20` |
| `ENTRY` | x,y | Entry cell coordinates | `ENTRY=0,0` |
| `EXIT` | x,y | Exit cell coordinates | `EXIT=39,19` |
| `OUTPUT_FILE` | string | Output filename (.txt only) | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | bool | If True, one unique path | `PERFECT=True` |
| `SEED` | int | Optional RNG seed | `SEED=42` |
| `ALGORITHM` | string | `DFS` or `PRIMS` | `ALGORITHM=PRIMS` |

---

## Output file format

```
FF9F...     ← hex row (one char per cell, all walls closed = F)
...

1,0         ← entry x,y
38,19       ← exit x,y
SENWS...    ← shortest path as N/E/S/W directions
```

---

## Maze generation algorithms

Two algorithms are available, selected via `ALGORITHM` in the config.

**Recursive DFS Backtracker (`ALGORITHM=DFS`)**

Starting from the entry cell, the algorithm visits unvisited neighbours in a random shuffled order, carving passages (removing shared walls) as it goes. When all neighbours are visited it backtracks. Produces mazes with long winding corridors.

**Prim's Algorithm (`ALGORITHM=PRIMS`)**

Maintains a frontier list of all cells reachable from any already-visited cell and picks one at random to connect. The maze grows outward in all directions simultaneously. Produces mazes with many short branches and a bushier texture.

Both algorithms always produce a perfect maze (spanning tree). The `SEED` option makes generation fully reproducible with either algorithm.

### Why these algorithms?

- Both are simple to implement and understand
- DFS produces long winding corridors — satisfying to solve
- Prim's produces a more organic, branchy structure
- Both naturally guarantee full connectivity (perfect maze)
- Both run in O(n) time and memory for n cells

---

## "42" pattern

Before DFS runs, cells forming the number "42" in a pixel font are marked as permanently walled (fully isolated). The DFS skips these cells, ensuring they appear as solid blocks in the output. If the maze is smaller than 10×9, a warning is printed and the pattern is omitted.

---

## Code reusability

The `maze/` package is installable as `mazegen-amazeing` via pip.

### Install from built package

```bash
pip install dist/mazegen_amazeing-1.0.0-py3-none-any.whl
```

### Basic usage

```python
from maze.config import MazeConfig
from maze.maze_generator import MazeGenerator
from maze.maze_solver import MazeSolver

cfg = MazeConfig(
    width=20, height=20,
    entry=(0, 0), exit=(19, 19),
    perfect=True,
    output_file="maze.txt",
    seed=42,
)

gen = MazeGenerator(cfg)
maze = gen.generate()       # List[List[int]] — bitmask per cell
gen.save_hex()              # writes maze.txt

solver = MazeSolver(maze, cfg)
path = solver.solve()       # list of (x, y) tuples
```

### Accessing the maze structure

Each cell is an integer with 4 bits:

| Bit | Value | Direction |
|-----|-------|-----------|
| 0 | 1 | North |
| 1 | 2 | East |
| 2 | 4 | South |
| 3 | 8 | West |

A set bit means the wall is **closed**. Example: `maze[0][0] & 1` is truthy if the north wall of cell (0,0) is present.

---

## Team & Project management

### Roles
- khhammou: display.py, a_maze_ing.py, _add_loops, bonus prim's algorithm, Makefile, bug fixes and testing
- mkhanji: config.py, maze_generator.py, maze_solver.py, pyproject.toml

### Planning
- Day 1–2: Config parser, maze generator, solver
- Day 3: Terminal display + interactive controls
- Day 4: "42" pattern, output file format, packaging
- Day 5: README, linting, edge cases

### What worked well
- The bitmask wall encoding is elegant and efficient
- BFS for solving guarantees the shortest path
- DFS and Prim's produce noticeably different maze textures from the same grid structure

### What could be improved
- `_add_loops()` currently only punches horizontal walls (EAST/WEST) — vertical walls should also be candidates for a more balanced imperfect maze
- MLX graphical display would be more visual

### Tools used
- Python 3.11, flake8, mypy, pytest
- Claude AI — used for code review, bug catching, and docstring generation

---

## Resources

- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Recursive backtracker — think-maths.co.uk](https://www.think-maths.co.uk/sites/default/files/2020-07/Maze%20worksheet.pdf)
- [Python dataclasses — docs.python.org](https://docs.python.org/3/library/dataclasses.html)
- [ANSI escape codes — Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)

### AI usage

Claude (Anthropic) was used for:
- Reviewing bug in `maze_solver.py` (unnamed 4th DIRS variable, silent empty-path return)
- Replacing DFS solver with BFS to guarantee shortest path
- Generating docstrings following PEP 257 / Google style
- Drafting the README structure
def _add_loops(self) -> None:
    w, h = self.config.width, self.config.height
    extra = (w * h) // 10

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