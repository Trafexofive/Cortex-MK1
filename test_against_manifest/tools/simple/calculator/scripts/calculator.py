#!/usr/bin/env python3
"""
Calculator Tool - Basic arithmetic operations
"""
import json
import sys


def add(a, b):
    """Add two numbers"""
    return a + b


def subtract(a, b):
    """Subtract b from a"""
    return a - b


def multiply(a, b):
    """Multiply two numbers"""
    return a * b


def divide(a, b):
    """Divide a by b"""
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b


def health_check():
    """Health check endpoint"""
    return {"status": "ok", "tool": "calculator", "version": "1.0"}


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "No JSON parameters provided"
        }))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        operation = params.get("operation")
        
        if operation == "health_check":
            result = health_check()
            print(json.dumps({"success": True, **result}))
            return
        
        # Get operands
        a = params.get("a")
        b = params.get("b")
        
        if a is None or b is None:
            print(json.dumps({
                "success": False,
                "error": "Both operands 'a' and 'b' are required"
            }))
            sys.exit(1)
        
        # Perform operation
        operations = {
            "add": add,
            "subtract": subtract,
            "multiply": multiply,
            "divide": divide
        }
        
        if operation not in operations:
            print(json.dumps({
                "success": False,
                "error": f"Unknown operation: {operation}"
            }))
            sys.exit(1)
        
        result = operations[operation](a, b)
        print(json.dumps({
            "success": True,
            "result": result,
            "operation": operation,
            "operands": {"a": a, "b": b}
        }))
    
    except ValueError as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)
    
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
