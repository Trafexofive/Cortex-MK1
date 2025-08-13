#!/usr/bin/env python3
import json
import os
import sys
import shutil
from pathlib import Path
import stat
import time

# Centralized logging (prints to stderr to avoid interfering with JSON stdout)
def log_message(level, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print(f"[{timestamp}] [{level}] unrestricted_fs_tool: {message}", file=sys.stderr)

def handle_create_file(params):
    path_str = params.get("path")
    content = params.get("content", "")
    overwrite = params.get("overwrite", False)

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if target_path.exists() and not overwrite:
            return {"success": False, "error": f"File '{path_str}' already exists and overwrite is false."}
        if target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' exists and is a directory."}
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        log_message("INFO", f"File created: {target_path.resolve()}")
        return {"success": True, "message": f"File '{path_str}' created successfully at '{target_path.resolve()}'."}
    except Exception as e:
        log_message("ERROR", f"Creating file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_read_file(params):
    path_str = params.get("path")
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"File '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_file():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a file."}
        
        content = target_path.read_text(encoding="utf-8")
        log_message("INFO", f"File read: {target_path.resolve()}")
        return {"success": True, "content": content, "path_resolved": str(target_path.resolve())}
    except Exception as e:
        log_message("ERROR", f"Reading file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_update_file(params):
    path_str = params.get("path")
    content = params.get("content")
    append = params.get("append", False)

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}
    if content is None:
        return {"success": False, "error": "Missing 'content' parameter."}

    try:
        target_path = Path(path_str)
        if target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is a directory, cannot update."}

        target_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(target_path, mode, encoding="utf-8") as f:
            f.write(content)
        log_message("INFO", f"File updated (mode: {'append' if append else 'overwrite'}): {target_path.resolve()}")
        return {"success": True, "message": f"File '{path_str}' updated successfully at '{target_path.resolve()}'."}
    except Exception as e:
        log_message("ERROR", f"Updating file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_delete_file(params):
    path_str = params.get("path")
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"File '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_file():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a file."}
        
        target_path.unlink()
        log_message("INFO", f"File deleted: {target_path.resolve()}")
        return {"success": True, "message": f"File '{path_str}' deleted successfully from '{target_path.resolve()}'."}
    except Exception as e:
        log_message("ERROR", f"Deleting file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_create_directory(params):
    path_str = params.get("path")
    parents = params.get("parents", True)

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if target_path.exists() and target_path.is_file():
             return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' exists and is a file."}
        
        target_path.mkdir(parents=parents, exist_ok=True)
        log_message("INFO", f"Directory created/ensured: {target_path.resolve()}")
        return {"success": True, "message": f"Directory '{path_str}' created/ensured successfully at '{target_path.resolve()}'."}
    except Exception as e:
        log_message("ERROR", f"Creating directory '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_list_directory(params):
    path_str = params.get("path", ".")
    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"Directory '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a directory."}

        items = []
        for item in target_path.iterdir():
            try:
                item_stat = item.stat()
                item_info = {
                    "name": item.name,
                    "path": str(item.resolve()),
                    "type": "directory" if item.is_dir() else "file",
                    "size_bytes": item_stat.st_size,
                    "modified_at_timestamp": int(item_stat.st_mtime),
                    "permissions": stat.filemode(item_stat.st_mode)
                }
                items.append(item_info)
            except Exception as item_e:
                log_message("WARNING", f"Could not stat item {item.name} in {path_str}: {item_e}")
                items.append({"name": item.name, "path": str(item.resolve()), "type": "unknown", "error": str(item_e)})
        
        log_message("INFO", f"Directory listed: {target_path.resolve()}")
        return {"success": True, "items": items, "path_resolved": str(target_path.resolve())}
    except Exception as e:
        log_message("ERROR", f"Listing directory '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_delete_directory(params):
    path_str = params.get("path")
    recursive = params.get("recursive", False)

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"Directory '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a directory."}

        if recursive:
            shutil.rmtree(target_path)
            log_message("INFO", f"Directory recursively deleted: {target_path.resolve()}")
            return {"success": True, "message": f"Directory '{path_str}' and its contents deleted from '{target_path.resolve()}'."}
        else:
            if any(target_path.iterdir()):
                return {"success": False, "error": f"Directory '{path_str}' at '{target_path.resolve()}' is not empty and recursive is false."}
            target_path.rmdir()
            log_message("INFO", f"Empty directory deleted: {target_path.resolve()}")
            return {"success": True, "message": f"Empty directory '{path_str}' deleted from '{target_path.resolve()}'."}
    except Exception as e:
        log_message("ERROR", f"Deleting directory '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_move_item(params):
    # Fixed: Check for both possible parameter names
    source_str = params.get("source_path") or params.get("source")
    destination_str = params.get("destination_path") or params.get("destination")

    if not source_str or not destination_str:
        missing_params = []
        if not source_str:
            missing_params.append("'source_path' or 'source'")
        if not destination_str:
            missing_params.append("'destination_path' or 'destination'")
        return {"success": False, "error": f"Missing {' and '.join(missing_params)} parameter(s)."}

    try:
        source_path = Path(source_str)
        destination_path = Path(destination_str)

        if not source_path.exists():
            return {"success": False, "error": f"Source '{source_str}' not found at '{source_path.resolve()}'."}
        
        # Ensure destination parent directory exists if moving to a new location
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(source_path), str(destination_path))
        log_message("INFO", f"Moved: {source_path.resolve()} -> {destination_path.resolve()}")
        return {"success": True, "message": f"Moved '{source_str}' to '{destination_str}'. Resolved: '{source_path.resolve()}' -> '{destination_path.resolve()}'"}
    except Exception as e:
        log_message("ERROR", f"Moving '{source_str}' to '{destination_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_copy_item(params):
    # Fixed: Check for both possible parameter names
    source_str = params.get("source_path") or params.get("source")
    destination_str = params.get("destination_path") or params.get("destination")

    if not source_str or not destination_str:
        missing_params = []
        if not source_str:
            missing_params.append("'source_path' or 'source'")
        if not destination_str:
            missing_params.append("'destination_path' or 'destination'")
        return {"success": False, "error": f"Missing {' and '.join(missing_params)} parameter(s)."}

    try:
        source_path = Path(source_str)
        destination_path = Path(destination_str)

        if not source_path.exists():
            return {"success": False, "error": f"Source '{source_str}' not found at '{source_path.resolve()}'."}

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_dir():
            shutil.copytree(str(source_path), str(destination_path), dirs_exist_ok=True)
        elif source_path.is_file():
            shutil.copy2(str(source_path), str(destination_path))
        else:
            return {"success": False, "error": f"Source '{source_str}' at '{source_path.resolve()}' is not a file or directory."}

        log_message("INFO", f"Copied: {source_path.resolve()} -> {destination_path.resolve()}")
        return {"success": True, "message": f"Copied '{source_str}' to '{destination_str}'. Resolved: '{source_path.resolve()}' -> '{destination_path.resolve()}'"}
    except Exception as e:
        log_message("ERROR", f"Copying '{source_str}' to '{destination_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_item_exists(params):
    path_str = params.get("path")
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}
    try:
        target_path = Path(path_str)
        exists = target_path.exists()
        item_type = "unknown"
        resolved_path_str = str(target_path.resolve())
        if exists:
            item_type = "directory" if target_path.is_dir() else "file" if target_path.is_file() else "other"
        log_message("INFO", f"Checked existence for: {resolved_path_str} (Exists: {exists}, Type: {item_type})")
        return {"success": True, "exists": exists, "type": item_type if exists else None, "path_resolved": resolved_path_str}
    except Exception as e:
        log_message("ERROR", f"Checking existence for '{path_str}': {e}")
        return {"success": False, "error": str(e), "exists": False}

def handle_get_item_info(params):
    path_str = params.get("path")
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}
    try:
        target_path = Path(path_str)
        resolved_path_str = str(target_path.resolve())

        if not target_path.exists():
            return {"success": False, "error": f"Item '{path_str}' not found at '{resolved_path_str}'."}

        item_stat = target_path.stat()
        info = {
            "name": target_path.name,
            "path_provided": path_str,
            "absolute_path": resolved_path_str,
            "type": "directory" if target_path.is_dir() else "file",
            "size_bytes": item_stat.st_size,
            "created_at_timestamp": int(item_stat.st_ctime),
            "modified_at_timestamp": int(item_stat.st_mtime),
            "accessed_at_timestamp": int(item_stat.st_atime),
            "permissions": stat.filemode(item_stat.st_mode),
            "owner_uid": item_stat.st_uid,
            "owner_gid": item_stat.st_gid,
        }
        log_message("INFO", f"Retrieved info for: {resolved_path_str}")
        return {"success": True, "info": info}
    except Exception as e:
        log_message("ERROR", f"Getting info for '{path_str}': {e}")
        return {"success": False, "error": str(e)}

OPERATION_HANDLERS = {
    "create_file": handle_create_file,
    "read_file": handle_read_file,
    "update_file": handle_update_file,
    "delete_file": handle_delete_file,
    "create_directory": handle_create_directory,
    "list_directory": handle_list_directory,
    "delete_directory": handle_delete_directory,
    "move_item": handle_move_item,
    "copy_item": handle_copy_item,
    "item_exists": handle_item_exists,
    "get_item_info": handle_get_item_info,
}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No JSON parameters provided."}))
        sys.exit(1)

    try:
        params_json_str = sys.argv[1]
        tool_params = json.loads(params_json_str) # This is the outer JSON structure
    except json.JSONDecodeError as e:
        log_message("CRITICAL", f"Invalid JSON parameters: {e}. Received: {params_json_str}")
        print(json.dumps({"success": False, "error": f"Invalid JSON input: {e}"}))
        sys.exit(1)

    operation = tool_params.get("operation")
    # The operation-specific parameters are now directly in tool_params
    # No separate "agent_workspace_path" or nested "params" object.

    if not operation:
        log_message("ERROR", "Operation parameter is missing.")
        print(json.dumps({"success": False, "error": "Missing 'operation' parameter."}))
        sys.exit(1)

    handler = OPERATION_HANDLERS.get(operation)
    if not handler:
        log_message("ERROR", f"Unknown operation: {operation}")
        print(json.dumps({"success": False, "error": f"Unknown operation: {operation}"}))
        sys.exit(1)
        
    try:
        # Pass the entire tool_params dict, as handlers now expect specific keys from it
        result = handler(tool_params) 
    except Exception as e:
        log_message("CRITICAL", f"Unhandled exception in operation '{operation}': {e}")
        result = {"success": False, "error": f"An unexpected error occurred during '{operation}': {e}"}

    print(json.dumps(result))

if __name__ == "__main__":
    main()
