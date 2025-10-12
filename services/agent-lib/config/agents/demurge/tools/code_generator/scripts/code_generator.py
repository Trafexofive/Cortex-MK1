#!/usr/bin/env python3
"""Code Generator Tool - Local to Demurge Agent"""
import json
import sys

TEMPLATES = {
    "python": {
        "hello_world": '''def hello_world():
    """Print hello world message."""
    print("Hello, World!")
    return "Success"

if __name__ == "__main__":
    hello_world()''',
        "fibonacci": '''def fibonacci(n):
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

if __name__ == "__main__":
    print(fibonacci(10))'''
    },
    "javascript": {
        "hello_world": '''function helloWorld() {
    console.log("Hello, World!");
    return "Success";
}

helloWorld();''',
        "fibonacci": '''function fibonacci(n) {
    if (n <= 0) return [];
    if (n === 1) return [0];
    
    const fib = [0, 1];
    for (let i = 2; i < n; i++) {
        fib.push(fib[i-1] + fib[i-2]);
    }
    return fib;
}

console.log(fibonacci(10));'''
    }
}

def generate_code(language, task, style="documented"):
    """Generate code based on parameters."""
    task_key = task.lower().replace(" ", "_")
    
    # Check if we have a template
    if language in TEMPLATES:
        if task_key in TEMPLATES[language]:
            code = TEMPLATES[language][task_key]
        elif "hello_world" in task.lower():
            code = TEMPLATES[language].get("hello_world", "# Template not found")
        elif "fibonacci" in task.lower() or "fib" in task.lower():
            code = TEMPLATES[language].get("fibonacci", "# Template not found")
        else:
            code = f"# Generated {language} code for: {task}\n# TODO: Implement {task}"
    else:
        code = f"// Code generation for {language} not yet implemented\n// Task: {task}"
    
    return {
        "code": code,
        "language": language,
        "task": task,
        "style": style,
        "lines": len(code.split('\n')),
        "chars": len(code)
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No parameters provided"}))
        sys.exit(1)
    
    try:
        params = json.loads(sys.argv[1])
        language = params.get("language", "python")
        task = params.get("task", "hello_world")
        style = params.get("style", "documented")
        
        result = generate_code(language, task, style)
        print(json.dumps({"success": True, "result": result}))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
