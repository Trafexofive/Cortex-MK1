#!/usr/bin/env python3
# config/scripts/core/generic_python_executor.py
import sys
import json
import subprocess
import os

# Define a base directory for allowed user scripts for security
# This should ideally be an absolute path configured robustly,
# or a path made canonical relative to a known project root.
# For this example, let's assume scripts are in a 'user_scripts' subdir
# relative to where generic_python_executor.py is located.
# THIS PATH CHECKING NEEDS TO BE VERY ROBUST IN A REAL SYSTEM.
ALLOWED_SCRIPT_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "user_scripts") # e.g. config/scripts/user_scripts/

def main():
    if len(sys.argv) < 2:
        print("CRITICAL_ERROR: generic_python_executor.py requires at least one argument (the JSON parameters string).", file=sys.stderr)
        sys.exit(1)

    params_json_str = sys.argv[1]

    try:
        params = json.loads(params_json_str)
    except json.JSONDecodeError as e:
        print(f"CRITICAL_ERROR: Invalid JSON parameters string provided: {e}", file=sys.stderr)
        print(f"Received: {params_json_str}", file=sys.stderr)
        sys.exit(1)

    target_script_relative_path = params.get("script_path")
    script_specific_params_obj = params.get("script_params", {}) # Default to empty dict

    if not target_script_relative_path or not isinstance(target_script_relative_path, str):
        print("CRITICAL_ERROR: 'script_path' string parameter is missing or invalid in JSON.", file=sys.stderr)
        sys.exit(1)

    # --- Security: Path Validation ---
    # Convert to absolute path and normalize
    # This base path should be the root of your allowed user scripts directory
    # Example: /home/mlamkadm/ai-repos/agents/agent-lib/config/scripts/user_scripts
    # Ensure ALLOWED_SCRIPT_BASE_DIR is an absolute, canonical path.
    # For this example, we calculate it relative to this executor script.
    # In a real app, configure this globally and pass it or make it well-known.
    
    # Ensure ALLOWED_SCRIPT_BASE_DIR is absolute and canonical for robust comparison
    abs_allowed_script_base_dir = os.path.abspath(ALLOWED_SCRIPT_BASE_DIR)
    
    # Resolve the target script path relative to the allowed base
    # os.path.join is safer than string concatenation for paths
    prospective_script_path = os.path.join(abs_allowed_script_base_dir, target_script_relative_path)
    
    # Normalize the path (resolve .., ., symlinks)
    abs_target_script_path = os.path.normpath(os.path.abspath(prospective_script_path))

    # Check if the resolved path is truly within the allowed base directory
    if not abs_target_script_path.startswith(abs_allowed_script_base_dir + os.sep) and abs_target_script_path != abs_allowed_script_base_dir :
        print(f"SECURITY_ERROR: Target script path '{target_script_relative_path}' resolves outside of the allowed base directory '{abs_allowed_script_base_dir}'. Resolved to '{abs_target_script_path}'. Execution denied.", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.exists(abs_target_script_path):
        print(f"CRITICAL_ERROR: Target script '{abs_target_script_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.isfile(abs_target_script_path):
        print(f"CRITICAL_ERROR: Target script path '{abs_target_script_path}' is not a file.", file=sys.stderr)
        sys.exit(1)
    # --- End Security: Path Validation ---


    # Pass script_specific_params_obj as a JSON string to the target script
    script_params_json_str_for_target = json.dumps(script_specific_params_obj)

    command = ["python3", abs_target_script_path, script_params_json_str_for_target]

    print(f"Executing Python script: {' '.join(command)}", file=sys.stderr) # Log for debugging

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # We will check returncode manually
            timeout=60  # Add a timeout for safety
        )

        if result.stdout:
            print(result.stdout.strip()) # This is the primary output for the agent

        if result.stderr:
            # Log stderr for debugging but don't necessarily fail the whole tool
            # unless returncode is non-zero.
            print(f"Script STDERR for {target_script_relative_path}:\n{result.stderr.strip()}", file=sys.stderr)

        if result.returncode != 0:
            print(f"ERROR: Target script {target_script_relative_path} exited with status {result.returncode}", file=sys.stderr)
            # The C++ side will typically capture stdout as the result.
            # If you want to signal error explicitly, stdout could contain an error message.
            # Or, the C++ side can check the overall executeScriptTool exit status.
            # For now, what's printed to stdout (even if an error message from the script) is returned.

    except subprocess.TimeoutExpired:
        print(f"ERROR: Target script {target_script_relative_path} timed out after 60 seconds.", file=sys.stderr)
        # Return an error message via stdout
        print(f"Error: Script {target_script_relative_path} timed out.")
        sys.exit(1) # Ensure non-zero exit for timeout
    except Exception as e:
        print(f"CRITICAL_ERROR: Failed to execute target Python script '{target_script_relative_path}': {e}", file=sys.stderr)
        # Return an error message via stdout
        print(f"Error: Could not execute script {target_script_relative_path} - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
