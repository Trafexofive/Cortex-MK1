#!/usr/bin/env python3
import json
import os
import sys
import shutil
import fnmatch
import glob
import re
import tempfile
import difflib
import base64
import zlib
import gzip
import io
from pathlib import Path
import stat
import time
import hashlib
from datetime import datetime
from collections import defaultdict

# Centralized logging (prints to stderr to avoid interfering with JSON stdout)
def log_message(level, message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print(f"[{timestamp}] [{level}] unrestricted_fs_tool: {message}", file=sys.stderr)

def handle_create_file(params):
    path_str = params.get("path")
    content = params.get("content", "")
    overwrite = params.get("overwrite", False)
    encoding = params.get("encoding", "utf-8")
    mode = params.get("mode")
    base64_encoded = params.get("base64_encoded", False)

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if target_path.exists() and not overwrite:
            return {"success": False, "error": f"File '{path_str}' already exists and overwrite is false."}
        if target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' exists and is a directory."}
        
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Handle binary content via base64
        if base64_encoded:
            try:
                binary_content = base64.b64decode(content)
                with open(target_path, "wb") as f:
                    f.write(binary_content)
            except Exception as be:
                return {"success": False, "error": f"Error decoding base64 content: {be}"}
        else:
            # Text content
            with open(target_path, "w", encoding=encoding) as f:
                f.write(content)
        
        # Set file permissions if specified
        if mode is not None:
            try:
                # Convert string like "644" to octal integer
                if isinstance(mode, str):
                    mode_int = int(mode, 8)
                else:
                    mode_int = mode
                os.chmod(target_path, mode_int)
            except Exception as mode_e:
                log_message("WARNING", f"Failed to set mode {mode} on {target_path}: {mode_e}")
        
        log_message("INFO", f"File created: {target_path.resolve()}")
        
        return {
            "success": True, 
            "message": f"File '{path_str}' created successfully at '{target_path.resolve()}'.",
            "path": str(target_path.resolve()),
            "size_bytes": target_path.stat().st_size
        }
    except Exception as e:
        log_message("ERROR", f"Creating file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_read_file(params):
    path_str = params.get("path")
    encoding = params.get("encoding", "utf-8")
    include_line_numbers = params.get("include_line_numbers", False)
    line_range = params.get("line_range")  # Format: "start-end" or "start-" or "-end"
    line_numbers = params.get("line_numbers")  # List of specific line numbers to read
    as_base64 = params.get("as_base64", False)
    head_lines = params.get("head", None)  # Get first N lines
    tail_lines = params.get("tail", None)  # Get last N lines
    
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"File '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_file():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a file."}
        
        file_size = target_path.stat().st_size
        
        # For binary files or when explicitly requested
        if as_base64:
            with open(target_path, "rb") as f:
                content = base64.b64encode(f.read()).decode('ascii')
                log_message("INFO", f"File read as base64: {target_path.resolve()} ({file_size} bytes)")
                return {
                    "success": True, 
                    "content": content, 
                    "encoding": "base64", 
                    "size_bytes": file_size,
                    "path_resolved": str(target_path.resolve())
                }
        
        # Process text files with line selections
        result = {"success": True, "path_resolved": str(target_path.resolve()), "size_bytes": file_size}
        
        # Handle different ways to read parts of files
        if head_lines is not None or tail_lines is not None or line_range is not None or line_numbers is not None:
            with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                all_lines = f.readlines()
                
            total_lines = len(all_lines)
            result["total_lines"] = total_lines
            
            if head_lines is not None:
                selected_lines = all_lines[:int(head_lines)]
                result["selection_type"] = "head"
                result["lines_selected"] = min(int(head_lines), total_lines)
                
            elif tail_lines is not None:
                selected_lines = all_lines[-int(tail_lines):]
                result["selection_type"] = "tail"
                result["lines_selected"] = min(int(tail_lines), total_lines)
                
            elif line_range is not None:
                parts = line_range.split('-')
                if len(parts) != 2:
                    return {"success": False, "error": "Invalid line_range format. Use 'start-end' or 'start-' or '-end'."}
                    
                start = int(parts[0]) - 1 if parts[0] else 0
                end = int(parts[1]) if parts[1] else total_lines
                
                # Validate range
                start = max(0, start)
                end = min(total_lines, end)
                
                selected_lines = all_lines[start:end]
                result["selection_type"] = "range"
                result["range"] = {"start": start + 1, "end": end}
                result["lines_selected"] = len(selected_lines)
                
            elif line_numbers is not None:
                selected_lines = []
                valid_lines = []
                
                for ln in line_numbers:
                    idx = int(ln) - 1  # Convert to 0-based index
                    if 0 <= idx < total_lines:
                        selected_lines.append(all_lines[idx])
                        valid_lines.append(ln)
                
                result["selection_type"] = "specific_lines"
                result["line_numbers"] = valid_lines
                result["lines_selected"] = len(selected_lines)
            
            # Format output with line numbers if requested
            if include_line_numbers:
                if head_lines is not None:
                    content = ''.join(f"{i+1}: {line}" for i, line in enumerate(selected_lines))
                elif tail_lines is not None:
                    start_idx = max(0, total_lines - int(tail_lines))
                    content = ''.join(f"{i+start_idx+1}: {line}" for i, line in enumerate(selected_lines))
                elif line_range is not None:
                    start = result["range"]["start"]
                    content = ''.join(f"{i+start}: {line}" for i, line in enumerate(selected_lines))
                elif line_numbers is not None:
                    content = ''.join(f"{ln}: {line}" for ln, line in zip(valid_lines, selected_lines))
            else:
                content = ''.join(selected_lines)
                
            result["content"] = content
            log_message("INFO", f"File read (partial): {target_path.resolve()} ({result['lines_selected']}/{total_lines} lines)")
            
        else:
            # Read the entire file
            if include_line_numbers:
                with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                    lines = f.readlines()
                    content = ''.join(f"{i+1}: {line}" for i, line in enumerate(lines))
                    result["total_lines"] = len(lines)
            else:
                content = target_path.read_text(encoding=encoding, errors='replace')
                result["total_lines"] = content.count('\n') + 1
                
            result["content"] = content
            log_message("INFO", f"File read (full): {target_path.resolve()}")
            
        return result
    except Exception as e:
        log_message("ERROR", f"Reading file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_read_directory_recursive(params):
    path_str = params.get("path", ".")
    pattern = params.get("pattern", "*")
    max_files = params.get("max_files", 100)
    max_depth = params.get("max_depth", 10)
    exclude_dirs = params.get("exclude_dirs", [])
    exclude_patterns = params.get("exclude_patterns", [])
    include_binary = params.get("include_binary", False)
    max_file_size_kb = params.get("max_file_size_kb", 1024)
    include_line_numbers = params.get("include_line_numbers", False)
    
    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"Directory '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a directory."}
        
        results = []
        file_count = 0
        size_limit = max_file_size_kb * 1024  # Convert to bytes
        
        # Helper to check if binary file
        def is_likely_binary(file_path):
            if not include_binary:
                # Check first 8KB of the file for null bytes
                with open(file_path, 'rb') as f:
                    chunk = f.read(8192)
                    if b'\x00' in chunk:
                        return True
                    # Check if over 30% non-ASCII characters
                    non_ascii = sum(1 for b in chunk if b < 32 or b > 126)
                    return non_ascii > len(chunk) * 0.3
            return False
        
        # Convert exclude_dirs to absolute paths
        exclude_dirs_abs = [str((target_path / d).resolve()) if not os.path.isabs(d) else d for d in exclude_dirs]
        
        # Helper function for recursive scan with depth control
        def scan_dir(current_path, current_depth):
            nonlocal file_count
            if current_depth > max_depth:
                return
            
            try:
                for item in current_path.iterdir():
                    # Check if should exclude
                    item_path_str = str(item.resolve())
                    if any(item_path_str.startswith(ex_dir) for ex_dir in exclude_dirs_abs):
                        continue
                    if any(fnmatch.fnmatch(item.name, pattern) for pattern in exclude_patterns):
                        continue
                    
                    if item.is_dir():
                        scan_dir(item, current_depth + 1)
                    elif item.is_file() and fnmatch.fnmatch(item.name, pattern):
                        if file_count >= max_files:
                            return
                        
                        try:
                            item_size = item.stat().st_size
                            if item_size > size_limit:
                                results.append({
                                    "path": str(item.relative_to(target_path)),
                                    "absolute_path": str(item.resolve()),
                                    "status": "skipped",
                                    "reason": f"File size ({item_size} bytes) exceeds limit ({size_limit} bytes)"
                                })
                                continue
                                
                            if is_likely_binary(item):
                                results.append({
                                    "path": str(item.relative_to(target_path)),
                                    "absolute_path": str(item.resolve()),
                                    "status": "skipped",
                                    "reason": "Appears to be binary file"
                                })
                                continue
                            
                            if include_line_numbers:
                                with open(item, 'r', encoding='utf-8', errors='replace') as f:
                                    lines = f.readlines()
                                    content = ''.join(f"{i+1}: {line}" for i, line in enumerate(lines))
                                    line_count = len(lines)
                            else:
                                content = item.read_text(encoding="utf-8", errors="replace")
                                line_count = content.count('\n') + 1
                                
                            results.append({
                                "path": str(item.relative_to(target_path)),
                                "absolute_path": str(item.resolve()),
                                "content": content,
                                "size_bytes": item_size,
                                "line_count": line_count,
                                "status": "read"
                            })
                            file_count += 1
                        except Exception as e:
                            results.append({
                                "path": str(item.relative_to(target_path)),
                                "absolute_path": str(item.resolve()),
                                "status": "error",
                                "error": str(e)
                            })
            except Exception as e:
                log_message("ERROR", f"Error scanning directory {current_path}: {e}")
        
        scan_dir(target_path, 0)
        
        log_message("INFO", f"Read {file_count} files recursively from: {target_path.resolve()}")
        return {
            "success": True, 
            "files": results,
            "stats": {
                "total_files_read": file_count,
                "max_files_limit": max_files,
                "max_depth": max_depth,
                "base_path": str(target_path.resolve())
            }
        }
    except Exception as e:
        log_message("ERROR", f"Reading directory recursively '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_search_files(params):
    path_str = params.get("path", ".")
    pattern = params.get("pattern", "*")  # File pattern (*.py, *.txt, etc)
    content_pattern = params.get("content_pattern")  # Optional text search
    recursive = params.get("recursive", True)
    case_sensitive = params.get("case_sensitive", False)
    max_results = params.get("max_results", 100)
    context_lines = params.get("context_lines", 0)  # Lines to show before/after match
    whole_word = params.get("whole_word", False)  # Match whole words only
    include_hidden = params.get("include_hidden", False)  # Include hidden files
    
    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"Path '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a directory."}
            
        # Compile regex pattern if content search is needed
        content_regex = None
        if content_pattern:
            flags = 0 if case_sensitive else re.IGNORECASE
            
            if whole_word:
                # Add word boundaries to the pattern
                content_pattern = r'\b' + content_pattern + r'\b'
                
            content_regex = re.compile(content_pattern, flags)
        
        results = []
        file_count = 0
        match_count = 0
        
        # Function to process a file for content matches
        def process_file(file_path):
            nonlocal match_count
            
            if match_count >= max_results:
                return False
                
            try:
                # Skip hidden files if not include_hidden
                if not include_hidden and file_path.name.startswith('.'):
                    return True
                
                if not content_regex:
                    # Just collecting files by pattern
                    results.append({
                        "path": str(file_path.relative_to(target_path)),
                        "absolute_path": str(file_path.resolve()),
                        "size_bytes": file_path.stat().st_size,
                        "matches": []
                    })
                    match_count += 1
                    return True
                else:
                    # Content search
                    matches = []
                    all_lines = []
                    
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        all_lines = f.readlines()
                    
                    # Process lines for matches
                    for line_num, line in enumerate(all_lines, 1):
                        if content_regex.search(line):
                            # Get context lines if requested
                            context = []
                            if context_lines > 0:
                                # Before lines
                                start = max(0, line_num - context_lines - 1)
                                before = [(i+start+1, all_lines[i+start]) for i in range(min(context_lines, line_num-1))]
                                
                                # After lines
                                end = min(len(all_lines), line_num + context_lines)
                                after = [(i+line_num, all_lines[i+line_num-1]) for i in range(1, end-line_num+1)]
                                
                                # Combine context
                                context = [{"line": line_num, "text": text, "type": "before"} for line_num, text in before]
                                context.extend([{"line": line_num, "text": text, "type": "after"} for line_num, text in after])
                            
                            # Create match entry
                            match_entry = {
                                "line_number": line_num,
                                "line": line.rstrip('\r\n'),
                            }
                            
                            if context_lines > 0:
                                match_entry["context"] = context
                                
                            matches.append(match_entry)
                            
                            if len(matches) + match_count >= max_results:
                                break
                    
                    if matches:
                        results.append({
                            "path": str(file_path.relative_to(target_path)),
                            "absolute_path": str(file_path.resolve()),
                            "size_bytes": file_path.stat().st_size,
                            "matches": matches,
                            "match_count": len(matches)
                        })
                        match_count += len(matches)
                        return True
            except Exception as e:
                log_message("WARNING", f"Error processing file {file_path}: {e}")
            return False
        
        # Find all matching files
        if recursive:
            for file_path in target_path.glob(f"**/{pattern}"):
                if file_path.is_file():
                    file_count += 1
                    if not process_file(file_path) or match_count >= max_results:
                        break
        else:
            for file_path in target_path.glob(pattern):
                if file_path.is_file():
                    file_count += 1
                    if not process_file(file_path) or match_count >= max_results:
                        break
        
        log_message("INFO", f"Search completed: {match_count} matches in {file_count} files from {target_path.resolve()}")
        return {
            "success": True,
            "results": results,
            "stats": {
                "files_examined": file_count,
                "match_count": match_count,
                "pattern": pattern,
                "content_pattern": content_pattern,
                "base_path": str(target_path.resolve()),
                "reached_limit": match_count >= max_results
            }
        }
    except Exception as e:
        log_message("ERROR", f"Searching files in '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_update_file(params):
    path_str = params.get("path")
    content = params.get("content")
    append = params.get("append", False)
    create_if_missing = params.get("create_if_missing", True)
    encoding = params.get("encoding", "utf-8")
    base64_encoded = params.get("base64_encoded", False)
    line_ending = params.get("line_ending")  # None, 'lf', 'crlf'
    backup = params.get("backup", False)  # Create backup before modifying
    insert_at_line = params.get("insert_at_line")  # Insert at specific line
    replace_line_range = params.get("replace_line_range")  # Replace lines in range (start-end)
    search_replace = params.get("search_replace")  # List of {search, replace} objects
    
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}
        
    # For simple append or overwrite, content is required
    if content is None and not search_replace and insert_at_line is None:
        return {"success": False, "error": "Missing 'content' parameter for append/overwrite operations."}

    try:
        target_path = Path(path_str)
        original_exists = target_path.exists()
        
        if original_exists and target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is a directory, cannot update."}
            
        if not original_exists and not create_if_missing:
            return {"success": False, "error": f"File '{path_str}' does not exist and create_if_missing is false."}
        
        # Create parent directories if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if requested
        if backup and original_exists:
            backup_path = target_path.with_suffix(target_path.suffix + '.bak')
            shutil.copy2(target_path, backup_path)
            log_message("INFO", f"Created backup: {backup_path}")
        
        # Handle different types of update operations
        if search_replace:
            # Text search and replace
            if not original_exists:
                return {"success": False, "error": f"File '{path_str}' does not exist for search/replace operation."}
                
            with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                file_content = f.read()
            
            original_content = file_content
            replacements_made = 0
            
            for sr in search_replace:
                search = sr.get("search")
                replace = sr.get("replace", "")
                count = sr.get("count", 0)  # 0 means replace all
                case_sensitive = sr.get("case_sensitive", False)
                
                if not search:
                    continue
                    
                if not case_sensitive:
                    # Case-insensitive replace using regex
                    pattern = re.compile(re.escape(search), re.IGNORECASE)
                    if count > 0:
                        new_content, num_replaced = pattern.subn(replace, file_content, count)
                    else:
                        new_content, num_replaced = pattern.subn(replace, file_content)
                else:
                    # Case-sensitive direct string replace
                    if count > 0:
                        new_content = file_content
                        for _ in range(count):
                            if search in new_content:
                                new_content = new_content.replace(search, replace, 1)
                                num_replaced += 1
                    else:
                        new_content = file_content.replace(search, replace)
                        num_replaced = file_content.count(search)
                
                file_content = new_content
                replacements_made += num_replaced
            
            # Only write if changes were made
            if original_content != file_content:
                with open(target_path, 'w', encoding=encoding) as f:
                    f.write(file_content)
                log_message("INFO", f"File updated with {replacements_made} replacements: {target_path.resolve()}")
            else:
                log_message("INFO", f"No changes made to file: {target_path.resolve()}")
            
            return {
                "success": True, 
                "message": f"File '{path_str}' updated with {replacements_made} replacements.",
                "replacements_made": replacements_made,
                "path": str(target_path.resolve())
            }
            
        elif insert_at_line is not None:
            # Line-based insertion
            line_num = int(insert_at_line)
            
            if original_exists:
                with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                    lines = f.readlines()
                
                # Ensure line_num is valid
                if line_num < 1:
                    line_num = 1
                elif line_num > len(lines) + 1:
                    line_num = len(lines) + 1
                
                # Convert 1-based to 0-based indexing
                idx = line_num - 1
                
                # Ensure content ends with newline if inserting between lines
                insert_content = content
                if idx < len(lines) and not content.endswith('\n'):
                    insert_content += '\n'
                
                # Insert the content
                lines.insert(idx, insert_content)
                
                with open(target_path, 'w', encoding=encoding) as f:
                    f.writelines(lines)
                
                log_message("INFO", f"Inserted content at line {line_num}: {target_path.resolve()}")
                return {
                    "success": True, 
                    "message": f"Content inserted at line {line_num} in '{path_str}'.",
                    "path": str(target_path.resolve())
                }
            else:
                # If file doesn't exist, just create it with the content
                with open(target_path, 'w', encoding=encoding) as f:
                    f.write(content)
                    
                log_message("INFO", f"Created new file with content: {target_path.resolve()}")
                return {
                    "success": True, 
                    "message": f"Created new file '{path_str}' with content.",
                    "path": str(target_path.resolve())
                }
                
        elif replace_line_range:
            # Replace specific lines
            if not original_exists:
                return {"success": False, "error": f"File '{path_str}' does not exist for line replacement operation."}
                
            # Parse the range
            try:
                range_parts = replace_line_range.split('-')
                start = int(range_parts[0])
                end = int(range_parts[1]) if len(range_parts) > 1 else start
            except Exception as re:
                return {"success": False, "error": f"Invalid replace_line_range format. Use 'start-end' or 'start': {re}"}
            
            # Read existing lines
            with open(target_path, 'r', encoding=encoding, errors='replace') as f:
                lines = f.readlines()
            
            # Validate range
            if start < 1:
                start = 1
            if end > len(lines):
                end = len(lines)
            if start > end:
                return {"success": False, "error": f"Invalid replace_line_range: start ({start}) must be <= end ({end})"}
            
            # Convert to 0-based indexing
            start_idx = start - 1
            end_idx = end - 1
            
            # Prepare replacement content
            if content.endswith('\n') and end_idx < len(lines) - 1:
                replacement_lines = content.splitlines(True)  # Keep newlines
            else:
                # Ensure proper line endings for the last line
                replacement_lines = content.splitlines()
                if end_idx < len(lines) - 1:  # Not replacing the last line
                    replacement_lines[-1] += '\n'
                    
            # Replace the lines
            new_lines = lines[:start_idx] + replacement_lines + lines[end_idx + 1:]
            
            with open(target_path, 'w', encoding=encoding) as f:
                f.writelines(new_lines)
            
            log_message("INFO", f"Replaced lines {start}-{end}: {target_path.resolve()}")
            return {
                "success": True, 
                "message": f"Replaced lines {start}-{end} in '{path_str}'.",
                "lines_replaced": end - start + 1,
                "path": str(target_path.resolve())
            }
            
        else:
            # Standard append or overwrite
            if base64_encoded:
                # Handle binary content
                try:
                    binary_content = base64.b64decode(content)
                    mode = "ab" if append else "wb"
                    with open(target_path, mode) as f:
                        f.write(binary_content)
                except Exception as be:
                    return {"success": False, "error": f"Error decoding base64 content: {be}"}
            else:
                # Text content
                mode = "a" if append else "w"
                with open(target_path, mode, encoding=encoding) as f:
                    # Apply line ending transformations if specified
                    if line_ending:
                        if line_ending == 'lf':
                            content = content.replace('\r\n', '\n')
                        elif line_ending == 'crlf':
                            # First normalize to LF, then convert to CRLF
                            content = content.replace('\r\n', '\n').replace('\n', '\r\n')
                    f.write(content)
            
            log_message("INFO", f"File updated (mode: {'append' if append else 'overwrite'}): {target_path.resolve()}")
            return {
                "success": True, 
                "message": f"File '{path_str}' updated successfully at '{target_path.resolve()}'.",
                "path": str(target_path.resolve()),
                "operation": "append" if append else "overwrite"
            }
    except Exception as e:
        log_message("ERROR", f"Updating file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_delete_file(params):
    path_str = params.get("path")
    pattern = params.get("pattern")  # Optional pattern for bulk delete
    safe_delete = params.get("safe_delete", False)  # Move to trash/recycle bin instead
    secure_wipe = params.get("secure_wipe", False)  # Overwrite before deleting
    wipe_passes = params.get("wipe_passes", 3)  # Number of wipe passes
    quiet = params.get("quiet", False)  # Don't error if file doesn't exist
    
    if not path_str and not pattern:
        return {"success": False, "error": "Either 'path' or 'pattern' parameter is required."}

    try:
        # Handle pattern-based deletion
        if pattern:
            target_dir = Path(path_str or ".")
            if not target_dir.exists() or not target_dir.is_dir():
                return {"success": False, "error": f"Directory '{target_dir}' not found or is not a directory."}
            
            matching_files = list(target_dir.glob(pattern))
            if not matching_files:
                message = f"No files matching pattern '{pattern}' found in '{target_dir}'."
                return {"success": True, "message": message, "deleted_count": 0} if quiet else {"success": False, "error": message}
            
            deleted_files = []
            failed_files = []
            
            for file_path in matching_files:
                if file_path.is_file():
                    try:
                        if secure_wipe:
                            secure_wipe_file(file_path, wipe_passes)
                        
                        if safe_delete:
                            # Implement platform-specific trash functionality
                            # For simplicity, we just move to a '.trash' directory in the current directory
                            trash_dir = target_dir / '.trash'
                            trash_dir.mkdir(exist_ok=True)
                            shutil.move(str(file_path), str(trash_dir / file_path.name))
                        else:
                            file_path.unlink()
                            
                        deleted_files.append(str(file_path))
                    except Exception as e:
                        failed_files.append({"path": str(file_path), "error": str(e)})
            
            log_message("INFO", f"Deleted {len(deleted_files)} files matching pattern '{pattern}' from {target_dir}")
            result = {
                "success": len(failed_files) == 0,
                "deleted_files": deleted_files,
                "deleted_count": len(deleted_files),
                "failed_count": len(failed_files)
            }
            
            if failed_files:
                result["failed_files"] = failed_files
            
            return result
        
        # Handle single file deletion
        target_path = Path(path_str)
        if not target_path.exists():
            if quiet:
                return {"success": True, "message": f"File '{path_str}' does not exist. No action taken."}
            return {"success": False, "error": f"File '{path_str}' not found at '{target_path.resolve()}'."}
        
        if not target_path.is_file():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a file."}
        
        if secure_wipe:
            secure_wipe_file(target_path, wipe_passes)
        
        if safe_delete:
            # Move to trash directory
            trash_dir = target_path.parent / '.trash'
            trash_dir.mkdir(exist_ok=True)
            shutil.move(str(target_path), str(trash_dir / target_path.name))
            log_message("INFO", f"File moved to trash: {target_path.name}")
            return {
                "success": True, 
                "message": f"File '{path_str}' moved to trash.",
                "trash_location": str(trash_dir / target_path.name)
            }
        else:
            target_path.unlink()
            log_message("INFO", f"File deleted: {target_path.resolve()}")
            return {"success": True, "message": f"File '{path_str}' deleted successfully from '{target_path.resolve()}'."}
    except Exception as e:
        log_message("ERROR", f"Deleting file '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def secure_wipe_file(file_path, passes=3):
    """Securely wipe a file by overwriting it multiple times before deletion"""
    try:
        file_size = file_path.stat().st_size
        
        # Skip for empty files
        if file_size == 0:
            return
            
        with open(file_path, "rb+") as f:
            for pass_num in range(passes):
                # Different patterns for each pass
                if pass_num == 0:
                    pattern = b'\x00'  # All zeros
                elif pass_num == 1:
                    pattern = b'\xFF'  # All ones
                else:
                    # Random data for other passes
                    pattern = os.urandom(1)
                
                # Seek to beginning of file
                f.seek(0)
                
                # Write pattern in chunks
                chunk_size = 8192
                for _ in range(0, file_size, chunk_size):
                    write_size = min(chunk_size, file_size - f.tell())
                    f.write(pattern * write_size)
                
                # Flush to disk
                f.flush()
                os.fsync(f.fileno())
    except Exception as e:
        log_message("WARNING", f"Secure wipe incomplete for {file_path}: {e}")
        # Continue with deletion anyway

def handle_create_directory(params):
    path_str = params.get("path")
    parents = params.get("parents", True)
    mode = params.get("mode")

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if target_path.exists() and target_path.is_file():
             return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' exists and is a file."}
        
        target_path.mkdir(parents=parents, exist_ok=True)
        
        # Set permissions if specified
        if mode is not None:
            try:
                # Convert string like "755" to octal integer
                if isinstance(mode, str):
                    mode_int = int(mode, 8)
                else:
                    mode_int = mode
                os.chmod(target_path, mode_int)
            except Exception as mode_e:
                log_message("WARNING", f"Failed to set mode {mode} on {target_path}: {mode_e}")
        
        log_message("INFO", f"Directory created/ensured: {target_path.resolve()}")
        return {
            "success": True, 
            "message": f"Directory '{path_str}' created/ensured successfully at '{target_path.resolve()}'.",
            "path": str(target_path.resolve())
        }
    except Exception as e:
        log_message("ERROR", f"Creating directory '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_list_directory(params):
    path_str = params.get("path", ".")
    include_stats = params.get("include_stats", True)
    include_hidden = params.get("include_hidden", False)
    sort_by = params.get("sort_by", "name")  # name, size, type, mtime
    sort_order = params.get("sort_order", "asc")  # asc, desc
    # Add support for recursive listing and content inclusion
    recursive = params.get("recursive", False)
    include_content = params.get("include_content", False)
    max_depth = params.get("max_depth", 10)
    pattern = params.get("pattern", "*")
    max_file_size_kb = params.get("max_file_size_kb", 1024)  # 1MB default limit
    include_line_numbers = params.get("include_line_numbers", False)
    
    try:
        target_path = Path(path_str)
        if not target_path.exists():
            return {"success": False, "error": f"Directory '{path_str}' not found at '{target_path.resolve()}'."}
        if not target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a directory."}

        items = []
        size_limit = max_file_size_kb * 1024  # Convert to bytes
        
        # Helper function for recursive directory traversal
        def process_directory(dir_path, current_depth=0):
            if current_depth > max_depth:
                return
                
            try:
                for item in dir_path.iterdir():
                    # Skip hidden files if not including them
                    if not include_hidden and item.name.startswith('.'):
                        continue
                        
                    try:
                        item_stat = item.stat()
                        item_type = "directory" if item.is_dir() else "file"
                        
                        # Create base item info
                        item_info = {
                            "name": item.name,
                            "path": str(item.relative_to(target_path)),
                            "absolute_path": str(item.resolve()),
                            "type": item_type,
                            "depth": current_depth,
                        }
                        
                        # Add stats if requested
                        if include_stats:
                            item_info.update({
                                "size_bytes": item_stat.st_size,
                                "modified_at_timestamp": int(item_stat.st_mtime),
                                "modified_at": datetime.fromtimestamp(item_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                                "permissions": stat.filemode(item_stat.st_mode)
                            })
                            
                            # Add extension for files
                            if item_type == "file":
                                item_info["extension"] = item.suffix.lower() if item.suffix else ""
                        
                        # Include file content if requested
                        if include_content and item_type == "file" and fnmatch.fnmatch(item.name, pattern):
                            try:
                                # Skip files exceeding size limit
                                if item_stat.st_size > size_limit:
                                    item_info["content_status"] = "skipped"
                                    item_info["content_reason"] = f"File size ({item_stat.st_size} bytes) exceeds limit ({size_limit} bytes)"
                                else:
                                    # Try to read file content
                                    if include_line_numbers:
                                        with open(item, 'r', encoding='utf-8', errors='replace') as f:
                                            lines = f.readlines()
                                            content = ''.join(f"{i+1}: {line}" for i, line in enumerate(lines))
                                            item_info["line_count"] = len(lines)
                                    else:
                                        content = item.read_text(encoding="utf-8", errors="replace")
                                        item_info["line_count"] = content.count('\n') + 1
                                        
                                    item_info["content"] = content
                                    item_info["content_status"] = "read"
                            except Exception as content_e:
                                item_info["content_status"] = "error"
                                item_info["content_error"] = str(content_e)
                        
                        items.append(item_info)
                        
                        # Recursively process subdirectories if requested
                        if recursive and item_type == "directory":
                            process_directory(item, current_depth + 1)
                            
                    except Exception as item_e:
                        log_message("WARNING", f"Could not process item {item.name} in {dir_path}: {item_e}")
                        items.append({
                            "name": item.name,
                            "path": str(item.relative_to(target_path)),
                            "absolute_path": str(item.resolve()),
                            "type": "unknown",
                            "error": str(item_e)
                        })
            except Exception as dir_e:
                log_message("ERROR", f"Error processing directory {dir_path}: {dir_e}")
        
        # Start processing from the target directory
        process_directory(target_path)
        
        # Sort items
        if sort_by == "name":
            items.sort(key=lambda x: x["name"].lower(), reverse=(sort_order == "desc"))
        elif sort_by == "size" and include_stats:
            items.sort(key=lambda x: x.get("size_bytes", 0), reverse=(sort_order == "desc"))
        elif sort_by == "type":
            items.sort(key=lambda x: x["type"], reverse=(sort_order == "desc"))
        elif sort_by == "mtime" and include_stats:
            items.sort(key=lambda x: x.get("modified_at_timestamp", 0), reverse=(sort_order == "desc"))
        elif sort_by == "depth":
            items.sort(key=lambda x: x.get("depth", 0), reverse=(sort_order == "desc"))
        
        # Prepare summary statistics
        file_count = sum(1 for item in items if item.get("type") == "file")
        dir_count = sum(1 for item in items if item.get("type") == "directory")
        
        summary = {
            "total_count": len(items),
            "file_count": file_count,
            "directory_count": dir_count,
            "total_size_bytes": sum(item.get("size_bytes", 0) for item in items if item.get("type") == "file"),
            "max_depth_found": max(item.get("depth", 0) for item in items) if items else 0
        }
        
        # Group by extension
        if include_stats:
            extensions = defaultdict(int)
            for item in items:
                if item.get("type") == "file" and "extension" in item:
                    ext = item["extension"] if item["extension"] else "(no extension)"
                    extensions[ext] += 1
            summary["extensions"] = dict(extensions)
        
        log_message("INFO", f"Directory listed: {target_path.resolve()} (recursive={recursive}, items={len(items)})")
        return {
            "success": True, 
            "items": items, 
            "path_resolved": str(target_path.resolve()),
            "recursive": recursive,
            "include_content": include_content,
            "summary": summary
        }
    except Exception as e:
        log_message("ERROR", f"Listing directory '{path_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_delete_directory(params):
    path_str = params.get("path")
    recursive = params.get("recursive", False)
    force = params.get("force", False)  # Delete even if not empty
    quiet = params.get("quiet", False)  # Don't error if directory doesn't exist
    safe_delete = params.get("safe_delete", False)  # Move to trash instead
    keep_permissions = params.get("keep_permissions", False)  # Preserve permissions for trash

    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}

    try:
        target_path = Path(path_str)
        if not target_path.exists():
            if quiet:
                return {"success": True, "message": f"Directory '{path_str}' does not exist. No action taken."}
            return {"success": False, "error": f"Directory '{path_str}' not found at '{target_path.resolve()}'."}
            
        if not target_path.is_dir():
            return {"success": False, "error": f"Path '{path_str}' at '{target_path.resolve()}' is not a directory."}

        if safe_delete:
            # Move to trash instead of deleting
            trash_dir = target_path.parent / '.trash'
            trash_dir.mkdir(exist_ok=True)
            
            # Create a unique name to avoid collisions
            trash_target = trash_dir / f"{target_path.name}_{int(time.time())}"
            
            # Use copy for recursive preservation if requested
            if recursive and keep_permissions:
                shutil.copytree(target_path, trash_target)
                shutil.rmtree(target_path)
            else:
                shutil.move(str(target_path), str(trash_target))
                
            log_message("INFO", f"Directory moved to trash: {target_path.resolve()} -> {trash_target}")
            return {
                "success": True, 
                "message": f"Directory '{path_str}' moved to trash at '{trash_target}'.",
                "trash_location": str(trash_target)
            }
        elif recursive or force:
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
    create_parents = params.get("create_parents", True)  # Create parent directories
    overwrite = params.get("overwrite", False)  # Overwrite destination if exists
    preserve_metadata = params.get("preserve_metadata", True)  # Preserve timestamps, etc.

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
            
        # Check if destination exists and we're not overwriting
        if destination_path.exists() and not overwrite:
            return {"success": False, "error": f"Destination '{destination_str}' already exists and overwrite is false."}
        
        # Ensure destination parent directory exists if moving to a new location
        if create_parents:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        if preserve_metadata:
            shutil.copy2(source_path, destination_path)
            if source_path.is_dir():
                shutil.rmtree(source_path)
            else:
                source_path.unlink()
        else:
            shutil.move(str(source_path), str(destination_path))
        
        log_message("INFO", f"Moved: {source_path.resolve()} -> {destination_path.resolve()}")
        return {
            "success": True, 
            "message": f"Moved '{source_str}' to '{destination_str}'. Resolved: '{source_path.resolve()}' -> '{destination_path.resolve()}'",
            "source": str(source_path.resolve()),
            "destination": str(destination_path.resolve())
        }
    except Exception as e:
        log_message("ERROR", f"Moving '{source_str}' to '{destination_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_copy_item(params):
    # Fixed: Check for both possible parameter names
    source_str = params.get("source_path") or params.get("source")
    destination_str = params.get("destination_path") or params.get("destination")
    create_parents = params.get("create_parents", True)  # Create parent directories
    overwrite = params.get("overwrite", False)  # Overwrite destination if exists
    preserve_metadata = params.get("preserve_metadata", True)  # Preserve timestamps, etc.
    symlinks = params.get("symlinks", False)  # Follow symlinks
    ignore_patterns = params.get("ignore_patterns", [])  # Patterns to ignore when copying directories

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
        
        # Check if destination exists and we're not overwriting
        if destination_path.exists() and not overwrite:
            return {"success": False, "error": f"Destination '{destination_str}' already exists and overwrite is false."}

        if create_parents:
            destination_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_dir():
            # Prepare ignore function for shutil.copytree
            ignore_func = None
            if ignore_patterns:
                ignore_func = shutil.ignore_patterns(*ignore_patterns)
                
            shutil.copytree(
                str(source_path), 
                str(destination_path), 
                symlinks=symlinks,
                ignore=ignore_func,
                dirs_exist_ok=True
            )
        elif source_path.is_file():
            if preserve_metadata:
                shutil.copy2(str(source_path), str(destination_path))
            else:
                shutil.copy(str(source_path), str(destination_path))
        else:
            return {"success": False, "error": f"Source '{source_str}' at '{source_path.resolve()}' is not a file or directory."}

        log_message("INFO", f"Copied: {source_path.resolve()} -> {destination_path.resolve()}")
        return {
            "success": True, 
            "message": f"Copied '{source_str}' to '{destination_str}'. Resolved: '{source_path.resolve()}' -> '{destination_path.resolve()}'",
            "source": str(source_path.resolve()),
            "destination": str(destination_path.resolve())
        }
    except Exception as e:
        log_message("ERROR", f"Copying '{source_str}' to '{destination_str}': {e}")
        return {"success": False, "error": str(e)}

def handle_item_exists(params):
    path_str = params.get("path")
    check_type = params.get("check_type")  # 'file', 'directory', or null for any
    
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}
    try:
        target_path = Path(path_str)
        exists = target_path.exists()
        item_type = "unknown"
        resolved_path_str = str(target_path.resolve())
        
        if exists:
            item_type = "directory" if target_path.is_dir() else "file" if target_path.is_file() else "other"
            
            # If check_type is specified, validate the type
            if check_type:
                type_valid = (check_type == "file" and item_type == "file") or \
                            (check_type == "directory" and item_type == "directory")
                            
                if not type_valid:
                    log_message("INFO", f"Item exists but wrong type: {resolved_path_str} (Required: {check_type}, Found: {item_type})")
                    return {
                        "success": True, 
                        "exists": True, 
                        "type": item_type, 
                        "type_valid": False,
                        "path_resolved": resolved_path_str
                    }
        
        log_message("INFO", f"Checked existence for: {resolved_path_str} (Exists: {exists}, Type: {item_type})")
        return {
            "success": True, 
            "exists": exists, 
            "type": item_type if exists else None, 
            "type_valid": exists and (not check_type or check_type == item_type),
            "path_resolved": resolved_path_str
        }
    except Exception as e:
        log_message("ERROR", f"Checking existence for '{path_str}': {e}")
        return {"success": False, "error": str(e), "exists": False}

def handle_get_item_info(params):
    path_str = params.get("path")
    calculate_hash = params.get("calculate_hash", False)
    hash_algorithm = params.get("hash_algorithm", "md5")
    include_mime_type = params.get("include_mime_type", False)  # Include MIME type
    preview_text_content = params.get("preview_text_content", False)  # Include first N lines
    preview_lines = params.get("preview_lines", 10)  # Number of lines to preview
    detailed_dir_info = params.get("detailed_dir_info", False)  # More directory stats
    
    if not path_str:
        return {"success": False, "error": "Missing 'path' parameter."}
    try:
        target_path = Path(path_str)
        resolved_path_str = str(target_path.resolve())

        if not target_path.exists():
            return {"success": False, "error": f"Item '{path_str}' not found at '{resolved_path_str}'."}

        item_stat = target_path.stat()
        is_dir = target_path.is_dir()
        
        info = {
            "name": target_path.name,
            "path_provided": path_str,
            "absolute_path": resolved_path_str,
            "parent_directory": str(target_path.parent.resolve()),
            "type": "directory" if is_dir else "file",
            "size_bytes": item_stat.st_size,
            "size_human": format_size_human(item_stat.st_size),
            "created_at_timestamp": int(item_stat.st_ctime),
            "modified_at_timestamp": int(item_stat.st_mtime),
            "accessed_at_timestamp": int(item_stat.st_atime),
            "created_at": datetime.fromtimestamp(item_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
            "modified_at": datetime.fromtimestamp(item_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "accessed_at": datetime.fromtimestamp(item_stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
            "permissions": stat.filemode(item_stat.st_mode),
            "permission_octal": oct(stat.S_IMODE(item_stat.st_mode))[2:],
            "owner_uid": item_stat.st_uid,
            "owner_gid": item_stat.st_gid,
        }
        
        # Get additional info for files
        if not is_dir:
            info["extension"] = target_path.suffix.lower() if target_path.suffix else ""
            
            # Try to detect text/binary and include mime type
            is_likely_text = True
            if include_mime_type:
                try:
                    import mimetypes
                    mime_type = mimetypes.guess_type(target_path)[0] or "application/octet-stream"
                    info["mime_type"] = mime_type
                    
                    # Basic check for binary file
                    if "text/" not in mime_type and not mime_type.startswith(("application/json", "application/xml")):
                        with open(target_path, 'rb') as f:
                            chunk = f.read(8192)
                            if b'\x00' in chunk:
                                is_likely_text = False
                            else:
                                # Check if over 30% non-ASCII characters
                                non_ascii = sum(1 for b in chunk if b < 32 or b > 126)
                                if non_ascii > len(chunk) * 0.3:
                                    is_likely_text = False
                except ImportError:
                    info["mime_type_error"] = "mimetypes module not available"
                except Exception as mime_e:
                    info["mime_type_error"] = str(mime_e)
            
            # Include text preview if requested and file is likely text
            if preview_text_content and is_likely_text:
                try:
                    with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
                        lines = [line.rstrip() for line in f.readlines()[:preview_lines]]
                        info["preview_content"] = "\n".join(lines)
                        info["preview_lines_count"] = len(lines)
                        info["total_lines"] = sum(1 for _ in open(target_path, 'r', encoding='utf-8', errors='replace'))
                except Exception as preview_e:
                    info["preview_error"] = str(preview_e)
            
            if calculate_hash and target_path.is_file():
                try:
                    hash_obj = None
                    if hash_algorithm == "md5":
                        hash_obj = hashlib.md5()
                    elif hash_algorithm == "sha1":
                        hash_obj = hashlib.sha1()
                    elif hash_algorithm == "sha256":
                        hash_obj = hashlib.sha256()
                    
                    if hash_obj:
                        with open(target_path, "rb") as f:
                            # Read in chunks to handle large files
                            for chunk in iter(lambda: f.read(4096), b""):
                                hash_obj.update(chunk)
                        info[f"{hash_algorithm}_hash"] = hash_obj.hexdigest()
                except Exception as hash_e:
                    info["hash_error"] = str(hash_e)
        else:
            # For directories
