#!/usr/bin/env python3
"""
Statistics Tool - Calculate statistical metrics
"""
import json
import sys
import statistics


def calculate_mean(data):
    """Calculate mean"""
    return statistics.mean(data)


def calculate_median(data):
    """Calculate median"""
    return statistics.median(data)


def calculate_stdev(data):
    """Calculate standard deviation"""
    return statistics.stdev(data) if len(data) > 1 else 0


def calculate_variance(data):
    """Calculate variance"""
    return statistics.variance(data) if len(data) > 1 else 0


def calculate_summary(data):
    """Calculate full statistical summary"""
    return {
        "count": len(data),
        "mean": calculate_mean(data),
        "median": calculate_median(data),
        "stdev": calculate_stdev(data),
        "variance": calculate_variance(data),
        "min": min(data),
        "max": max(data),
        "range": max(data) - min(data)
    }


def health_check():
    """Health check"""
    return {"status": "ok", "tool": "stats_tool"}


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
            return
        
        data = params.get("data", [])
        if not data:
            print(json.dumps({"success": False, "error": "Data array is required"}))
            sys.exit(1)
        
        if not all(isinstance(x, (int, float)) for x in data):
            print(json.dumps({"success": False, "error": "All data must be numeric"}))
            sys.exit(1)
        
        if operation == "mean":
            result = {"result": calculate_mean(data)}
        elif operation == "median":
            result = {"result": calculate_median(data)}
        elif operation == "stdev":
            result = {"result": calculate_stdev(data)}
        elif operation == "variance":
            result = {"result": calculate_variance(data)}
        elif operation == "summary":
            result = {"summary": calculate_summary(data)}
        else:
            print(json.dumps({"success": False, "error": f"Unknown operation: {operation}"}))
            sys.exit(1)
        
        print(json.dumps({"success": True, **result}))
    
    except statistics.StatisticsError as e:
        print(json.dumps({"success": False, "error": f"Statistics error: {str(e)}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
