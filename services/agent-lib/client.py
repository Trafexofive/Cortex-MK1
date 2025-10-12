import curses
import requests
import json
import textwrap
from datetime import datetime
import argparse
import shlex # For robust command argument parsing
import time
import os # For clearing screen before starting curses

# --- Configuration ---
DEFAULT_SERVER_URL = "http://localhost:7777"

class AgentTUI:
    def __init__(self, stdscr, server_url):
        self.stdscr = stdscr
        self.server_url = server_url.rstrip('/')
        self.agent_name = "Agent" # Will be updated by /agent/info

        # Curses Initialization
        curses.curs_set(1) # Show cursor
        self.stdscr.nodelay(False) # Blocking input
        self.stdscr.keypad(True)   # Enable special keys (arrows, etc.)
        # self.stdscr.timeout(100) # Optional: Add a small timeout to getch to allow non-blocking checks

        # Colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)  # User
        curses.init_pair(2, curses.COLOR_BLUE, -1)   # Agent
        curses.init_pair(3, curses.COLOR_RED, -1)    # Error/System Error
        curses.init_pair(4, curses.COLOR_YELLOW, -1) # Status/System Info
        curses.init_pair(5, curses.COLOR_CYAN, -1)   # Command Output/Success
        curses.init_pair(6, curses.COLOR_WHITE, -1)  # Default text
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_WHITE) # Status Bar Highlight

        self.USER_COLOR = curses.color_pair(1)
        self.AGENT_COLOR = curses.color_pair(2)
        self.ERROR_COLOR = curses.color_pair(3)
        self.STATUS_COLOR = curses.color_pair(4)
        self.CMD_OUTPUT_COLOR = curses.color_pair(5)
        self.DEFAULT_COLOR = curses.color_pair(6)
        self.STATUS_HIGHLIGHT_COLOR = curses.color_pair(7)


        self.chat_history = []
        self.input_buffer = ""
        self.display_lines_cache = [] # Cache of wrapped lines for scrolling
        self.history_view_top_index = 0 # Index in display_lines_cache that is at the top of history_win

        self.is_running = True
        self.setup_windows() # Initial setup
        self.fetch_initial_agent_info()

    def setup_windows(self):
        self.height, self.width = self.stdscr.getmaxyx()
        if self.height < 5 or self.width < 20: # Basic check for too small terminal
            # Cannot proceed with curses if terminal is too small
            raise Exception("Terminal too small. Minimum 20x5 required.")


        # Status window (top)
        self.status_win_height = 1
        self.status_win = curses.newwin(self.status_win_height, self.width, 0, 0)
        self.status_win.bkgd(' ', self.STATUS_HIGHLIGHT_COLOR) # Set background for status bar

        # History window (middle)
        # -1 for status_win, -1 for border, -1 for input_win
        self.history_win_height = self.height - self.status_win_height - 2
        if self.history_win_height < 1: self.history_win_height = 1 # Ensure at least 1 line

        self.history_win = curses.newwin(self.history_win_height, self.width, self.status_win_height + 1, 0)
        self.history_win.scrollok(True)
        self.history_win.idlok(True)

        # Input window (bottom)
        self.input_win_height = 1
        self.input_win = curses.newwin(self.input_win_height, self.width, self.height - 1, 0)
        self.input_win.keypad(True)

        self.redraw_all_ui_elements() # Full redraw after setup

    def redraw_all_ui_elements(self):
        self.stdscr.clear() # Clear whole screen
        self.stdscr.refresh()

        # Draw border line between status and history
        try:
            # Ensure y-coordinate is within screen bounds
            border_y = self.status_win_height
            if 0 <= border_y < self.height:
                 self.stdscr.hline(border_y, 0, curses.ACS_HLINE, self.width)
        except curses.error: pass # Ignore if it fails (e.g. tiny terminal)
        self.stdscr.refresh() # Refresh stdscr after drawing border

        self.update_status_bar()
        self._prepare_display_lines_cache() # Recalculate wrapped lines based on new width
        self.render_history_content()
        self.render_input_buffer_content()

    def update_status_bar(self, message=None, is_error=False):
        self.status_win.clear()
        status_text = ""
        if message:
            status_text = message
        else:
            status_text = f"Agent: {self.agent_name} | URL: {self.server_url} | Type '/help' for commands."
        
        status_text = status_text[:self.width-1] # Truncate
        bar_color = self.ERROR_COLOR if is_error else self.STATUS_HIGHLIGHT_COLOR
        
        try:
            self.status_win.bkgd(' ', bar_color) # Set background for entire status bar
            self.status_win.addstr(0, 0, status_text, bar_color)
        except curses.error: pass # Ignore if error during status update (e.g. during resize)
        self.status_win.refresh()

    def fetch_initial_agent_info(self):
        try:
            data = self._api_get("/agent/info")
            if data and "name" in data:
                old_name = self.agent_name
                self.agent_name = data["name"]
                if old_name != self.agent_name:
                     self.add_message_to_history("SYS_INFO", f"Agent name updated to: {self.agent_name}", self.STATUS_COLOR)
            else:
                self.add_message_to_history("SYS_ERROR", f"Connected, but couldn't get agent name. Response: {str(data)[:100]}", self.ERROR_COLOR)
        except Exception as e:
            self.add_message_to_history("SYS_ERROR", f"Failed to connect or get initial agent info: {e}", self.ERROR_COLOR)
        self.update_status_bar()

    def add_message_to_history(self, sender, text, color, add_timestamp=True):
        timestamp_str = datetime.now().strftime("%H:%M:%S") if add_timestamp else "       " # 7 spaces for alignment
        self.chat_history.append((timestamp_str, sender, text, color))
        self._prepare_display_lines_cache()
        # Auto-scroll to bottom on new message
        self.history_view_top_index = max(0, len(self.display_lines_cache) - self.history_win_height)
        if hasattr(self, 'history_win') and self.history_win: # Check if window exists
             self.render_history_content()

    def _prepare_display_lines_cache(self):
        self.display_lines_cache = []
        # Max width for text content in history window, leaving space for timestamp, sender, and padding.
        # Roughly: Timestamp (8) + Space (1) + Sender (max ~15) + ColonSpace (2) + Text + Padding (1)
        # For simplicity, we'll use a fixed offset for prefix and wrap the rest.
        # A more dynamic calculation based on actual sender length could be used.
        prefix_max_len = 8 + 1 + 15 + 2 # ts + space + sender + ": "
        text_area_width = self.width - prefix_max_len -1 # -1 for safety margin

        if text_area_width < 10: # If window too small, just show truncated text
            text_area_width = 10 

        for ts, sender, text, color in self.chat_history:
            prefix = f"[{ts}] {sender[:15]}: " # Truncate sender if too long
            
            # Handle cases where the text itself might be None or not a string
            if not isinstance(text, str):
                text = str(text)

            wrapped_text_lines = textwrap.wrap(text, width=text_area_width, drop_whitespace=True, replace_whitespace=False, fix_sentence_endings=False)

            if not wrapped_text_lines: # If text was empty or only whitespace
                self.display_lines_cache.append(((prefix.rstrip(), color)))
            else:
                self.display_lines_cache.append(((prefix + wrapped_text_lines[0], color)))
                indent = " " * len(prefix)
                for line_content in wrapped_text_lines[1:]:
                    self.display_lines_cache.append(((indent + line_content, color)))
        
    def render_history_content(self):
        if not hasattr(self, 'history_win') or not self.history_win: return
        self.history_win.clear()
        
        self.history_view_top_index = max(0, min(self.history_view_top_index, max(0, len(self.display_lines_cache) - self.history_win_height)))

        for i in range(self.history_win_height):
            display_line_idx = self.history_view_top_index + i
            if 0 <= display_line_idx < len(self.display_lines_cache):
                line_text, color = self.display_lines_cache[display_line_idx]
                try:
                    # Truncate line_text to fit window width exactly, preventing addstr error
                    self.history_win.addstr(i, 0, line_text[:self.width], color)
                except curses.error:
                    try: # Fallback if color causes issue or line still too long
                        self.history_win.addstr(i, 0, line_text[:self.width], self.DEFAULT_COLOR)
                    except: pass # Skip line if it still errors
        self.history_win.refresh()

    def render_input_buffer_content(self):
        if not hasattr(self, 'input_win') or not self.input_win: return
        self.input_win.clear()
        prompt = "> "
        
        available_width_for_text = self.width - len(prompt) - 1 # -1 for cursor itself
        if available_width_for_text < 0 : available_width_for_text = 0

        buffer_display_start_index = 0
        if len(self.input_buffer) > available_width_for_text:
            buffer_display_start_index = len(self.input_buffer) - available_width_for_text
        
        displayed_buffer = self.input_buffer[buffer_display_start_index:]
        
        try:
            self.input_win.addstr(0, 0, prompt)
            self.input_win.addstr(0, len(prompt), displayed_buffer)
            self.input_win.move(0, len(prompt) + len(displayed_buffer)) # Position cursor correctly
        except curses.error: pass
        self.input_win.refresh()

    def _api_get(self, endpoint):
        self.update_status_bar(f"GET {endpoint}...", is_error=False)
        try:
            response = requests.get(f"{self.server_url}{endpoint}", timeout=15)
            self.update_status_bar() 
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            self.add_message_to_history("SYS_ERROR", f"API GET Timeout: {endpoint}", self.ERROR_COLOR)
        except requests.exceptions.ConnectionError:
            self.add_message_to_history("SYS_ERROR", f"API GET Connection Error: {endpoint}. Server running?", self.ERROR_COLOR)
        except requests.exceptions.HTTPError as e:
            err_msg = f"API GET HTTP Error: {endpoint} ({e.response.status_code})"
            try: err_msg += f" - {e.response.json().get('error', e.response.text[:100])}"
            except: err_msg += f" - {e.response.text[:100]}"
            self.add_message_to_history("SYS_ERROR", err_msg, self.ERROR_COLOR)
        except json.JSONDecodeError as e:
            res_text = response.text[:100] if hasattr(response, 'text') else "N/A"
            self.add_message_to_history("SYS_ERROR", f"API GET JSON Decode Error: {endpoint} - {e} - Response: {res_text}", self.ERROR_COLOR)
        except Exception as e:
            self.add_message_to_history("SYS_ERROR", f"Unexpected error GET {endpoint}: {type(e).__name__} - {e}", self.ERROR_COLOR)
        self.update_status_bar(f"GET {endpoint} failed", is_error=True)
        return None

    def _api_post(self, endpoint, payload=None):
        self.update_status_bar(f"POST {endpoint}...", is_error=False)
        actual_payload = payload if payload is not None else {}
        try:
            # Default timeout for agent potentially long operations
            timeout = 60 if endpoint == "/prompt" else 20 
            response = requests.post(f"{self.server_url}{endpoint}", json=actual_payload, timeout=timeout)
            self.update_status_bar()
            response.raise_for_status()
            if response.status_code == 204: 
                return {"status": "success", "message": f"Operation {endpoint} OK (No Content)"}
            if response.text:
                return response.json()
            return {"status": "success", "message": f"Operation {endpoint} OK (empty response body)"}
        except requests.exceptions.Timeout:
            self.add_message_to_history("SYS_ERROR", f"API POST Timeout: {endpoint}", self.ERROR_COLOR)
        except requests.exceptions.ConnectionError:
            self.add_message_to_history("SYS_ERROR", f"API POST Connection Error: {endpoint}. Server running?", self.ERROR_COLOR)
        except requests.exceptions.HTTPError as e:
            err_msg = f"API POST HTTP Error: {endpoint} ({e.response.status_code})"
            try: err_msg += f" - {e.response.json().get('error', e.response.text[:100])}"
            except: err_msg += f" - {e.response.text[:100]}"
            self.add_message_to_history("SYS_ERROR", err_msg, self.ERROR_COLOR)
        except json.JSONDecodeError as e:
            res_text = response.text[:100] if hasattr(response, 'text') else "N/A"
            self.add_message_to_history("SYS_ERROR", f"API POST JSON Decode Error: {endpoint} - {e} - Response: {res_text}", self.ERROR_COLOR)
        except Exception as e:
            self.add_message_to_history("SYS_ERROR", f"Unexpected error POST {endpoint}: {type(e).__name__} - {e}", self.ERROR_COLOR)
        self.update_status_bar(f"POST {endpoint} failed", is_error=True)
        return None

    def _handle_scroll_input(self, direction, amount=None):
        if amount is None:
            amount = self.history_win_height // 2 
            if amount < 1: amount = 1
        
        if direction == "up":
            self.history_view_top_index = max(0, self.history_view_top_index - amount)
        elif direction == "down":
            self.history_view_top_index = min(max(0, len(self.display_lines_cache) - self.history_win_height), 
                                                 self.history_view_top_index + amount)
        elif direction == "top":
             self.history_view_top_index = 0
        elif direction == "bottom":
             self.history_view_top_index = max(0, len(self.display_lines_cache) - self.history_win_height)
        
        self.render_history_content()

    def process_tui_command_input(self, command_line):
        try:
            parts = shlex.split(command_line)
        except ValueError as e:
            self.add_message_to_history("SYS_ERROR", f"Error parsing command: {e}. Check quotes.", self.ERROR_COLOR)
            return

        if not parts: return
        
        command = parts[0].lower()
        args = parts[1:]

        # Simple echo of the command being processed
        self.add_message_to_history("SYS_CMD", f"Executing: {command_line}", self.CMD_OUTPUT_COLOR)

        if command == "/quit" or command == "/exit":
            self.is_running = False
            return

        elif command == "/help":
            help_text = """TUI Commands:
  /prompt <text>             - Send prompt (or just type text & Enter).
  /info                      - Get agent's current configuration.
  /history                   - Fetch agent's server-side conversation history.
  /config <json_payload>     - Update agent config (e.g., /config {"name":"NewDemurge"}).
  /tool <name> <json_params> - Execute tool (e.g., /tool bash {"command":"ls"}).
  /reset                     - Reset agent's state on server.
  /clear                     - Clear local TUI chat display.
  /scroll <up|down|top|bottom> [N] - Scroll by N lines (default half screen).
  /help                      - Show this help. /quit or /exit to exit."""
            self.add_message_to_history("SYSTEM", help_text, self.DEFAULT_COLOR, add_timestamp=False)

        elif command == "/clear":
            self.chat_history = []
            self._prepare_display_lines_cache()
            self.history_view_top_index = 0
            self.render_history_content()
            self.add_message_to_history("SYSTEM", "Local TUI history cleared.", self.STATUS_COLOR)


        elif command == "/info":
            data = self._api_get("/agent/info")
            if data:
                if "name" in data and self.agent_name != data["name"]:
                    self.agent_name = data["name"]
                    self.update_status_bar()
                pretty_json = json.dumps(data, indent=2)
                self.add_message_to_history("CMD_RESP", f"Agent Info:\n{pretty_json}", self.CMD_OUTPUT_COLOR)

        elif command == "/history":
            data = self._api_get("/agent/history")
            if data and "history" in data:
                self.add_message_to_history("CMD_RESP", "--- Agent Server History (Last 10, Newest First) ---", self.CMD_OUTPUT_COLOR, add_timestamp=False)
                for entry in reversed(data["history"][-10:]):
                    self.add_message_to_history(f"SRV_HIST ({entry.get('role')})", entry.get("content", ""), self.CMD_OUTPUT_COLOR, add_timestamp=True)
                self.add_message_to_history("CMD_RESP", "--- End Agent Server History ---", self.CMD_OUTPUT_COLOR, add_timestamp=False)

        elif command == "/config":
            if not args:
                self.add_message_to_history("SYS_ERROR", "Usage: /config <json_payload>", self.ERROR_COLOR)
                return
            json_payload_str = " ".join(args)
            try:
                payload = json.loads(json_payload_str)
                response_data = self._api_post("/agent/config", payload)
                if response_data:
                    self.add_message_to_history("CMD_RESP", f"Config Response: {json.dumps(response_data)}", self.CMD_OUTPUT_COLOR)
                    time.sleep(0.2) 
                    self.fetch_initial_agent_info() 
            except json.JSONDecodeError:
                self.add_message_to_history("SYS_ERROR", "Invalid JSON payload for /config.", self.ERROR_COLOR)

        elif command == "/tool":
            if len(args) < 1:
                self.add_message_to_history("SYS_ERROR", "Usage: /tool <tool_name> [json_params]", self.ERROR_COLOR)
                return
            tool_name = args[0]
            params_payload_str = " ".join(args[1:]) if len(args) > 1 else "{}"
            try:
                params = json.loads(params_payload_str)
                response_data = self._api_post(f"/agent/tools/{tool_name}/execute", params)
                if response_data:
                    result_text = response_data.get('result', json.dumps(response_data))
                    if isinstance(result_text, str) and (result_text.startswith('{') or result_text.startswith('[')):
                        try: result_text = json.dumps(json.loads(result_text), indent=2)
                        except: pass 
                    elif isinstance(result_text, dict) or isinstance(result_text, list):
                        result_text = json.dumps(result_text, indent=2)
                    self.add_message_to_history("CMD_RESP", f"Tool '{tool_name}' Result:\n{result_text}", self.CMD_OUTPUT_COLOR)
            except json.JSONDecodeError:
                self.add_message_to_history("SYS_ERROR", f"Invalid JSON parameters for /tool {tool_name}.", self.ERROR_COLOR)
        
        elif command == "/reset":
            response_data = self._api_post("/agent/reset")
            if response_data:
                self.add_message_to_history("CMD_RESP", f"Agent Reset Response: {json.dumps(response_data)}", self.CMD_OUTPUT_COLOR)
                self.add_message_to_history("SYSTEM", "Agent state reset on server.", self.STATUS_COLOR)


        elif command == "/scroll":
            s_dir = args[0] if args else "down"
            s_amount_str = args[1] if len(args) > 1 else None
            s_amount = None
            if s_amount_str and s_amount_str.isdigit():
                s_amount = int(s_amount_str)
            elif s_amount_str:
                 self.add_message_to_history("SYS_ERROR", f"Invalid scroll amount: {s_amount_str}. Must be a number.", self.ERROR_COLOR)
                 return
            self._handle_scroll_input(s_dir, s_amount)
            
        else:
            self.add_message_to_history("SYS_ERROR", f"Unknown command: {command}. Type /help.", self.ERROR_COLOR)
        
    def run_main_loop(self):
        self.add_message_to_history("SYSTEM", f"Welcome! Connected to Agent Server: {self.server_url}", self.STATUS_COLOR)
        
        while self.is_running:
            self.render_input_buffer_content()
            
            try:
                # Using getch for more responsive input, but get_wch is better for unicode
                # char_code = self.input_win.get_wch() # Prefer get_wch
                char_code = self.input_win.getch() # Using getch for wider compatibility with simple terminals
            except curses.error as e:
                # If timeout is set on input_win, this might catch timeout errors as curses.error
                # if "no input" in str(e).lower(): # Check for timeout specifically if timeout set on window
                #    time.sleep(0.01) # Short sleep on timeout
                #    continue
                time.sleep(0.05) 
                continue
            except KeyboardInterrupt:
                 self.add_message_to_history("SYSTEM", "Ctrl+C detected. Type /quit or /exit to exit.", self.STATUS_COLOR)
                 continue

            if char_code == curses.KEY_RESIZE:
                self.height, self.width = self.stdscr.getmaxyx()
                try:
                    # Resize windows before redrawing
                    self.status_win.resize(self.status_win_height, self.width)
                    
                    new_hist_h = self.height - self.status_win_height - 2
                    if new_hist_h < 1: new_hist_h = 1
                    self.history_win_height = new_hist_h
                    self.history_win.resize(self.history_win_height, self.width)
                    
                    self.input_win.resize(self.input_win_height, self.width)
                    self.input_win.mvwin(self.height - 1, 0) # Ensure input_win is at bottom

                    self.redraw_all_ui_elements()
                except curses.error: pass # Ignore errors during resize flurry
                continue

            elif char_code == curses.KEY_ENTER or char_code == 10 or char_code == 13:
                if self.input_buffer.strip():
                    line_to_process = self.input_buffer.strip()
                    # Add to history *before* clearing for command processing
                    # self.add_message_to_history("User", line_to_process, self.USER_COLOR) 
                    
                    self.input_buffer = "" 
                    
                    if line_to_process.startswith("/"):
                        self.process_tui_command_input(line_to_process)
                    else:
                        self.add_message_to_history("User", line_to_process, self.USER_COLOR) # Show user input
                        self.add_message_to_history(self.agent_name, "Thinking...", self.AGENT_COLOR) # Thinking message
                        self.render_history_content() # Update history to show "Thinking..."
                        self.update_status_bar(f"Sending to {self.agent_name}...")

                        response_data = self._api_post("/prompt", {"prompt": line_to_process})
                        
                        # Remove "Thinking..." 
                        if self.chat_history and self.chat_history[-1][1] == self.agent_name and self.chat_history[-1][2] == "Thinking...":
                            self.chat_history.pop()
                            # Don't need to _prepare_display_lines_cache yet, will be done by next add_message
                        
                        if response_data and "response" in response_data:
                            self.add_message_to_history(self.agent_name, response_data["response"], self.AGENT_COLOR)
                        elif response_data and "error" in response_data:
                            self.add_message_to_history("SYS_ERROR", f"Agent Error: {response_data['error']} {response_data.get('details','')}", self.ERROR_COLOR)
                        # Other API errors are handled by _api_post and add messages directly
                self.render_input_buffer_content() # Refresh input line

            elif char_code == curses.KEY_BACKSPACE or char_code == 127 or char_code == 8: # 8 is ASCII BS
                self.input_buffer = self.input_buffer[:-1]
            elif char_code == curses.KEY_UP:
                self._handle_scroll_input("up", 1)
            elif char_code == curses.KEY_DOWN:
                self._handle_scroll_input("down", 1)
            elif char_code == curses.KEY_PPAGE: 
                self._handle_scroll_input("up")
            elif char_code == curses.KEY_NPAGE: 
                self._handle_scroll_input("down")
            elif char_code == curses.KEY_HOME:
                self._handle_scroll_input("top")
            elif char_code == curses.KEY_END:
                self._handle_scroll_input("bottom")
            elif 32 <= char_code <= 126 or char_code > 127: # Printable ASCII and potentially other UTF-8 chars
                # getch returns int, convert to char for string append
                try:
                    char_to_add = chr(char_code)
                    if len(self.input_buffer) < self.width - 4: 
                        self.input_buffer += char_to_add
                except ValueError: pass # Invalid chr code, ignore

def main_curses_app_runner(stdscr):
    # Clear screen before curses init (optional, but can help)
    # print("\033c", end="") # Or os.system('cls' if os.name == 'nt' else 'clear')
    # curses.wrapper usually handles this, but an explicit clear can be cleaner.

    global args_namespace # Use the global parsed args
    if args_namespace is None: # Should not happen if main calls correctly
        parser_temp = argparse.ArgumentParser()
        parser_temp.add_argument("--url", default=DEFAULT_SERVER_URL)
        args_namespace = parser_temp.parse_args([]) # Default if not passed

    tui = AgentTUI(stdscr, args_namespace.url)
    tui.run_main_loop()

args_namespace = None 

if __name__ == "__main__":
    # It's cleaner to parse args before curses.wrapper
    parser = argparse.ArgumentParser(description="TUI Client for C++ Agent Server")
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_SERVER_URL,
        help=f"Base URL of the agent API server (default: {DEFAULT_SERVER_URL})"
    )
    args_namespace = parser.parse_args() # Store in global for curses_wrapper context

    try:
        # Clear terminal before starting curses
        # This helps if previous output messed up the terminal
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
            
        curses.wrapper(main_curses_app_runner)
    except curses.error as e:
        # This will catch errors if curses.wrapper fails or if AgentTUI init fails badly
        print(f"A Curses error occurred: {e}")
        print("Your terminal might be in an inconsistent state. Try running 'reset'.")
    except requests.exceptions.ConnectionError as e:
        print(f"FATAL: Could not connect to server at {args_namespace.url if args_namespace else DEFAULT_SERVER_URL}.")
        print(f"Ensure the agent server is running. Details: {e}")
    except Exception as e:
        print(f"TUI Client exited with an unexpected error: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors
    finally:
        # curses.wrapper should handle cleanup, but this is a fallback.
        try:
            if curses.isendwin() is False:
                curses.nocbreak()
                curses.echo()
                curses.endwin()
        except Exception as final_e:
            print(f"Error during final curses cleanup: {final_e}")
        print("TUI client closed.")
