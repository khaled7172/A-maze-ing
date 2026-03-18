"""Configuration module for the maze generator.

Defines the MazeConfig dataclass and the load_config parser.
"""

from dataclasses import dataclass


@dataclass
class MazeConfig:
    """Hold all parameters needed to generate and save a maze.

    Attributes:
        width: Number of cells horizontally.
        height: Number of cells vertically.
        entry: (x, y) coordinates of the maze entrance.
        exit: (x, y) coordinates of the maze exit.
        perfect: If True, exactly one path exists between entry and exit.
        output_file: Path to write the hex-encoded maze output.
        seed: Optional RNG seed for reproducibility.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    perfect: bool
    output_file: str
    seed: int | None = None


def load_config(config: str) -> MazeConfig:
    """Read a config file and return a MazeConfig object.

    Args:
        config: Path to the configuration file.

    Returns:
        A fully validated MazeConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the file contains invalid or missing keys.
    """
    try:
        with open(config) as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: '{config}'")

    temp_config: dict = {}

    for line in lines:
        line = line.strip()
        if line == "" or line.startswith('#'):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid line in config (missing '='): {line!r}")

        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()

        if key == "WIDTH":
            temp_config["width"] = int(value)
        elif key == "HEIGHT":
            temp_config["height"] = int(value)
        elif key == "ENTRY":
            temp_config["entry"] = tuple(map(int, value.split(",")))
        elif key == "EXIT":
            temp_config["exit"] = tuple(map(int, value.split(",")))
        elif key == "PERFECT":
            if value.lower() == "true":
                temp_config["perfect"] = True
            elif value.lower() == "false":
                temp_config["perfect"] = False
            else:
                raise ValueError("PERFECT must be 'True' or 'False'")
        elif key == "OUTPUT_FILE":
            parts = value.split(".", 1)
            if len(parts) < 2:
                raise ValueError("OUTPUT_FILE must have a file extension")
            if parts[1] != "txt":
                raise ValueError("OUTPUT_FILE must be a .txt file")
            temp_config["output_file"] = value
        elif key == "SEED":
            temp_config["seed"] = int(value)

    required = ["width", "height", "entry", "exit", "perfect", "output_file"]
    for k in required:
        if k not in temp_config:
            raise ValueError(f"Missing required config key: '{k.upper()}'")

    width = temp_config["width"]
    height = temp_config["height"]
    ex, ey = temp_config["entry"]
    ox, oy = temp_config["exit"]

    if width <= 0 or height <= 0:
        raise ValueError("WIDTH and HEIGHT must be positive integers")
    if not (0 <= ex < width and 0 <= ey < height):
        raise ValueError(
            f"ENTRY ({ex},{ey}) is out of bounds for maze {width}x{height}"
        )
    if not (0 <= ox < width and 0 <= oy < height):
        raise ValueError(
            f"EXIT ({ox},{oy}) is out of bounds for maze {width}x{height}"
        )
    if (ex, ey) == (ox, oy):
        raise ValueError("ENTRY and EXIT cannot be the same cell")

    return MazeConfig(
        width=width,
        height=height,
        entry=temp_config["entry"],
        exit=temp_config["exit"],
        perfect=temp_config["perfect"],
        output_file=temp_config["output_file"],
        seed=temp_config.get("seed"),
    )
