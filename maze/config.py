##dataclass hold data values with main benefit when generating special method --init--

from dataclasses import dataclass

@dataclass
##save from writing them manually.
class MazeConfig:
  width :int
  height :int
  entry : tuple[int , int]
  exit : tuple[int , int]
  perfect : bool #exactly one path between the entry and exit no loops.
  output_file: str
  seed: int | None = None #to make maze generation reproducible.

def load_config(config : str):
  """
  Reads config.txt and returns a MazeConfig object.
  """
  with open(config) as f:
    lines = f.readlines()
  temp_config = {}
  for line in lines:
    line = line.strip()
    if line == "" or line.startswith('#'):
      continue
    if "=" not in line:
      raise ValueError(f"Invalid line in config: {line}")
    key, value = line.split("=", 1)
    key = key.strip().upper()
    value = value.strip()

    if key == " WIDTH":
      temp_config["width"] = int(value)
    elif key == "HEIGHT":
      temp_config["height"] = int(value)
    elif key == "ENTRY":
      temp_config["entry"] = tuple(map(int, value.split(",")))
    elif key == "EXIT":
      temp_config["exit"] = tuple(map(int , value.split(",")))
    elif key == "PERFECT":
      temp_config["perfect"] = value.lower() == "true"
    elif key == "OUTPUT_FILE":
      temp_config["output_file"] = value
    elif key == "SEED":
      temp_config["seed"] = int(value)
    else:
      pass #unknown
  required = ["width", "height", "entry", "exit", "perfect", "output_file"] 
  for k in required:
    if not k in temp_config:
      raise ValueError(f"Missing required config: {key}")

  width = temp_config["width"]
  height = temp_config["height"]
  ex, ey = temp_config["entry"]
  ox, oy = temp_config["exit"]
  if not (0 <= ex < width and 0 <= ey < height):
      raise ValueError("Entry point out of bounds")
  if not (0 <= ox < width and 0 <= oy < height):
      raise ValueError("Exit point out of bounds")
  if (ex, ey) == (ox, oy):
      raise ValueError("Entry and exit cannot be the same")

  print("Config file opened successfully")
  return MazeConfig(
        width=temp_config["width"],
        heigh=temp_config["height"], 
        entry=temp_config["entry"],
        exit=temp_config["exit"],
        perfect=temp_config["perfect"],
        output_file=temp_config["output_file"],
        seed=temp_config.get("seed")
    )