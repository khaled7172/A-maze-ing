"""Configuration module for the maze generator.

Defines the MazeConfig dataclass and the load_config parser.
"""

from dataclasses import dataclass

"""
This creates a class, its like a blue print for storing maze settings
@dataclass is a decorator, it automatically generates the __init__ method
for you so you dont have to write def __init__(self, width,...)
"""


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
    entry: tuple[int, int]  # means entry must be a tuple containing 2 ints
    exit: tuple[int, int]
    perfect: bool
    output_file: str
    #  seed is to make maze generation reproducible, its optional and
    #  defaults to None if not available
    seed: int | None = None
    algorithm: str = "DFS"


"""
This function takes one argument, the config, which is expected to be the
filename called with load_config("config.txt")
"""


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
    """
    Reads config.txt and returns a MazeConfig object.
    open (config) opens the file, and the with keyword makes sure the file
    gets automatically closed after even if something goes wrong
    f.readdlines() reads every line and stores them as a list of strings,
    so lines looks like: ["WIDTH=20\n", "HEIGHT=15\n", ...]
    """
    try:
        with open(config) as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: '{config}'")
    """
    This is an empty dict, think of it as a temporary storage box, as we
    reach each line we'll drop the values here before building the
    MazeConfig object
    """
    temp_config: dict = {}
    """
    we go through each line one by one, .strip() removes whitespace and \n
    from both ends if the lines is empty or a comment we skip it entirely,
    continues jumps to next iteration of the loop
    if a line doesn't have an equal in it, something is wrong raise error and
    stop program
    line.split("=", 1) cuts the line at the = sign into 2 pieces,
    1 means split only once, then we unpack them into key and value
    """
    for line in lines:
        line = line.strip()
        if line == "" or line.startswith('#'):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid line in config (missing '='): {line!r}")

        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()

        """
        we check what the key is, then store the value in temp_config
        value from file is always a string so we cast to an int
        for entry we do a split first at the , which puts the 2 values into
        list items then we use the map() function to convert every string
        into an int then we wrap it into a tuple
        """

        if key == "WIDTH":
            temp_config["width"] = int(value)
        elif key == "HEIGHT":
            temp_config["height"] = int(value)
        elif key == "ENTRY":
            x, y = value.split(",")
            temp_config["entry"] = (int(x), int(y))
        elif key == "EXIT":
            x, y = value.split(",")
            temp_config["exit"] = (int(x), int(y))
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
        elif key == "ALGORITHM":
            if value.upper() not in ("DFS", "PRIMS"):
                raise ValueError("ALGORITHM must be 'DFS' or 'PRIMS'")
            temp_config["algorithm"] = value.upper()

    """
    This creates a list of all the keys that must be present.
    Then loops through them and checks if each one made it into temp_config
    If something is missing it raises an error
    """
    required = ["width", "height", "entry", "exit", "perfect", "output_file"]
    for k in required:
        if k not in temp_config:
            raise ValueError(f"Missing required config key: '{k.upper()}'")

    """
    This unpacks the coordinates and checks three things
    If Entry is inside the grid
    If exit is inside the grid
    they're not the same point
    """

    width = temp_config["width"]
    height = temp_config["height"]
    ex, ey = temp_config["entry"]
    ox, oy = temp_config["exit"]

    if width <= 0 or height <= 0:
        raise ValueError("WIDTH and HEIGHT must be positive integers")
    if not (0 <= ex < width and 0 <= ey < height):
        raise ValueError(
            f"ENTRY ({ex},{ey}) is out of bounds for maze {width}x{height}")
    if not (0 <= ox < width and 0 <= oy < height):
        raise ValueError(
            f"EXIT ({ox},{oy}) is out of bounds for maze {width}x{height}")
    if (ex, ey) == (ox, oy):
        raise ValueError("ENTRY and EXIT cannot be the same cell")

    """
    This create the final MazeConfig object and returns it
    """
    return MazeConfig(
        width=width,
        height=height,
        entry=temp_config["entry"],
        exit=temp_config["exit"],
        perfect=temp_config["perfect"],
        output_file=temp_config["output_file"],
        seed=temp_config.get("seed"),
        algorithm=temp_config.get("algorithm", "DFS"),
    )
