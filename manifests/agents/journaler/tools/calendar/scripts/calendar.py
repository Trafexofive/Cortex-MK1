#!/usr/bin/env python3
import json
import sys
from datetime import datetime

def get_current_date():
    return {"current_date": datetime.now().strftime("%Y-%m-%d")}

def get_current_time():
    return {"current_time": datetime.now().strftime("%H:%M:%S")}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No JSON parameters provided."}))
        sys.exit(1)

    try:
        params = json.loads(sys.argv[1])
        operation = params.get("operation")

        if operation == "get_current_date":
            result = get_current_date()
        elif operation == "get_current_time":
            result = get_current_time()
        else:
            result = {"success": False, "error": f"Unknown operation: {operation}"}
        
        print(json.dumps({"success": True, "result": result}))

    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
