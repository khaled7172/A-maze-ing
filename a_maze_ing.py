from maze.config import load_config

def main():
  config = load_config("config.txt")
  print(config)

main()