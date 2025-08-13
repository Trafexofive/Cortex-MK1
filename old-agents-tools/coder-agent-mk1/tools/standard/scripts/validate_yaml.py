import yaml
import sys

file_path = sys.argv[1]

try:
    with open(file_path, 'r') as f:
        yaml.safe_load(f)
    print(f"YAML file '{file_path}' is valid.")
    sys.exit(0)
except yaml.YAMLError as e:
    print(f"YAML parsing error in '{file_path}': {e}")
    sys.exit(1)
except FileNotFoundError:
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)
