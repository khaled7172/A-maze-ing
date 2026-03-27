"""Entry point for the A-Maze-ing maze generator.

Usage:
    python3 a_maze_ing.py config.txt
"""

import sys
from maze.config import MazeConfig, load_config
from maze.maze_generator import MazeGenerator
from maze.maze_solver import MazeSolver
from maze.display import interactive


def build_maze(
    config: MazeConfig,
    seed: int | None = None,
) -> tuple[list[list[int]], list[tuple[int, int]], set[tuple[int, int]]]:
    """Build a complete maze: generate, solve, and save to file.

    If seed is provided a fresh MazeConfig is created with that seed,
    used when the user presses 'r' to regenerate in interactive mode.

    Args:
        config: Base maze configuration.
        seed: Optional override seed for regeneration.

    Returns:
        Tuple of (maze grid, solution path, set of '42' pattern cells).
    """
    if seed is not None:
        config = MazeConfig(
            width=config.width,
            height=config.height,
            entry=config.entry,
            exit=config.exit,
            perfect=config.perfect,
            output_file=config.output_file,
            seed=seed,
            algorithm=config.algorithm,
        )

    gen = MazeGenerator(config)
    maze = gen.generate()

    solver = MazeSolver(maze, config)
    solution = solver.solve()

    gen.save_hex(solution_path=solution)

    cells_42: set[tuple[int, int]] = set(gen._42_cells)
    return maze, solution, cells_42


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
    except (ValueError, RuntimeError) as e:
        print(f"Maze generation error: {e}", file=sys.stderr)
        sys.exit(1)

    def maze_factory(
        seed: int,
    ) -> tuple[list[list[int]], list[tuple[int, int]], set[tuple[int, int]]]:
        """Re-generate maze with a new seed for interactive re-draw.

        Args:
            seed: New seed value.

        Returns:
            Tuple of (maze grid, solution path, set of '42' pattern cells).
        """
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
