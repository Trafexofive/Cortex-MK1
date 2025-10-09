#!/usr/bin/env python3
"""
Calculator Tool - Safe mathematical expression evaluator
"""

import sys
import json
import math
import ast
import operator

# Safe operators
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe functions
FUNCTIONS = {
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'abs': abs,
    'round': round,
    'floor': math.floor,
    'ceil': math.ceil,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
}

# Safe constants
CONSTANTS = {
    'pi': math.pi,
    'e': math.e,
}


def safe_eval(node):
    """Safely evaluate an AST node."""
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Name):
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise ValueError(f"Undefined variable: {node.id}")
    elif isinstance(node, ast.BinOp):
        op = OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported operator: {type(node.op)}")
        return op(safe_eval(node.left), safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op = OPERATORS.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported operator: {type(node.op)}")
        return op(safe_eval(node.operand))
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")
        func = FUNCTIONS.get(node.func.id)
        if not func:
            raise ValueError(f"Unsupported function: {node.func.id}")
        args = [safe_eval(arg) for arg in node.args]
        return func(*args)
    elif isinstance(node, ast.Expression):
        return safe_eval(node.body)
    else:
        raise ValueError(f"Unsupported operation: {type(node)}")


def calculate(expression: str) -> dict:
    """Calculate the result of a mathematical expression."""
    try:
        # Parse the expression
        tree = ast.parse(expression, mode='eval')
        
        # Evaluate safely
        result = safe_eval(tree)
        
        return {
            "status": "success",
            "result": result,
            "expression": expression
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "expression": expression
        }


def main():
    """Main entry point."""
    try:
        # Read input from stdin or first argument
        if len(sys.argv) > 1:
            input_data = json.loads(sys.argv[1])
        else:
            input_data = json.load(sys.stdin)
        
        expression = input_data.get("expression")
        if not expression:
            print(json.dumps({"status": "error", "error": "Missing 'expression' parameter"}))
            sys.exit(1)
        
        result = calculate(expression)
        print(json.dumps(result))
        
        # Exit with error code if calculation failed
        sys.exit(0 if result["status"] == "success" else 1)
        
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
