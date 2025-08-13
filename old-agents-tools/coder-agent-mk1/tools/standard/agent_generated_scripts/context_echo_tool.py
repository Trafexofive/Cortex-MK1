#!/usr/bin/env python3
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("Error: Parameters required.", file=sys.stderr)
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON parameters: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({"received_params": params, "success": True}))

if __name__ == "__main__":
    main()
