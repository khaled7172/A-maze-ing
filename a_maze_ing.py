import sys
from typing import List, Tuple

from maze.config import MazeConfig, load_config
from maze.maze_generator import MazeGenerator
from maze.maze_solver import MazeSolver
from maze.display import interactive

"""
This function builds a complete maze and returns 3 things
maze grid, solution path, and the "42" cells
If a new seed is passed in, it creates a fresh MazeConfig with that seed
this is used when the user presses r to regenerate in the interactive display
Then it runs everything in order
generate
solve
save
"""


def build_maze(
    config: MazeConfig,
    seed: int | None = None,
) -> tuple[List[List[int]], List[Tuple[int, int]], set[tuple[int, int]]]:

    if seed is not None:
        config = MazeConfig(
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit=config.exit,
            perfect=config.perfect,
            output_file=config.output_file,
            seed=seed,
        )

    gen = MazeGenerator(config)
    maze = gen.generate()

    solver = MazeSolver(maze, config)
    solution = solver.solve()

    gen.save_hex(solution_path=solution)

    cells_42: set[tuple[int, int]] = set(gen._42_cells)
    return maze, solution, cells_42


"""
sys.argv is the list of command line arguments
sys.argv[0] is always the script name
sys.argv[1] is the config file
if ont exactly one argument it prints usage and exits
then it loads the config, builds the maze
launches the interactive display
maze_factory is a small fucntion passed to interactive so it can regenerate
the maze when the user presses r
"""


def main() -> None:
    """Entry point: parse args, build maze, launch interactive display."""
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)
        sys.exit(1)

    try:
        config = load_config(sys.argv[1])
    except (FileNotFoundError, ValueError) as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        maze, solution, cells_42 = build_maze(config)
    except (ValueError, RecursionError) as e:
        print(f"Maze generation error: {e}", file=sys.stderr)
        sys.exit(1)

    # print(f"{config}")
    # print(f"solution  {solution}")

    def maze_factory(
            seed: int) -> tuple[List[List[int]], List[Tuple[int, int]],
                                set[tuple[int, int]]]:
        """Re-generate maze with a new seed for interactive re-draw."""
        return build_maze(config, seed=seed)

    interactive(
        maze_factory=maze_factory,
        config=config,
        initial_maze=maze,
        initial_solution=solution,
        initial_42=cells_42,
    )


if __name__ == "__main__":
    main()
