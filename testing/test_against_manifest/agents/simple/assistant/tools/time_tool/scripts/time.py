#!/usr/bin/env python3
"""
Time Tool - Get current date and time
"""
import json
import sys
from datetime import datetime


def get_time():
    """Get current time"""
    return datetime.now().strftime("%H:%M:%S")


def get_date():
    """Get current date"""
    return datetime.now().strftime("%Y-%m-%d")


def get_datetime():
    """Get current datetime"""
    return datetime.now().isoformat()


def health_check():
    """Health check"""
    return {"status": "ok", "tool": "time_tool"}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No parameters provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        operation = params.get("operation")
        
        if operation == "health_check":
            result = health_check()
            print(json.dumps({"success": True, **result}))
        elif operation == "get_time":
            print(json.dumps({"success": True, "time": get_time()}))
        elif operation == "get_date":
            print(json.dumps({"success": True, "date": get_date()}))
        elif operation == "get_datetime":
            print(json.dumps({"success": True, "datetime": get_datetime()}))
        else:
            print(json.dumps({"success": False, "error": f"Unknown operation: {operation}"}))
            sys.exit(1)
    
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
