import sys
import json

def main():
    params = json.loads(sys.argv[1])
    operation = params.get("operation")

    if operation == "transcribe":
        # Echo the input for testing purposes
        text_input = params.get("text_input", "")
        print(json.dumps({"success": True, "transcript": text_input}))
    elif operation == "synthesize":
        # Echo the input for testing purposes
        text_input = params.get("text_input", "")
        print(json.dumps({"success": True, "response_text": text_input}))
    else:
        print(json.dumps({"success": False, "error": f"Unknown operation: {operation}"}))

if __name__ == "__main__":
    main()