#!/usr/bin/env python3
"""
Cortex-Prime CLI - Simple chat interface
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8085"
AGENT_NAME = "assistant"  # Default agent


class Colors:
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


async def create_session(agent_name: str):
    """Create a new agent session."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/agent/{agent_name}/session",
            json={"user_id": "cli_user", "metadata": {}}
        )
        response.raise_for_status()
        return response.json()


async def send_message(session_id: str, message: str):
    """Send message and stream response."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/agent/session/{session_id}/message",
            json={"content": message, "stream": True}
        ) as response:
            print(f"{Colors.BLUE}Assistant:{Colors.RESET} ", end="", flush=True)
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        chunk_type = data.get("type")
                        chunk_data = data.get("data")
                        
                        if chunk_type == "content":
                            print(chunk_data, end="", flush=True)
                        elif chunk_type == "tool_call":
                            print(f"\n{Colors.YELLOW}[Tool: {chunk_data.get('name')}]{Colors.RESET}", end="", flush=True)
                        elif chunk_type == "error":
                            print(f"\n{Colors.RED}Error: {chunk_data.get('error')}{Colors.RESET}")
                    except json.JSONDecodeError:
                        pass
            
            print()  # Newline after response


async def chat_loop(agent_name: str):
    """Main chat loop."""
    print(f"{Colors.CYAN}{Colors.BOLD}Cortex-Prime CLI{Colors.RESET}")
    print(f"Agent: {agent_name}")
    print(f"Commands: /quit, /new (new session)\n")
    
    # Create session
    try:
        session = await create_session(agent_name)
        session_id = session["session_id"]
        print(f"{Colors.GREEN}Session created: {session_id}{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}Failed to create session: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Is the agent_orchestrator running? (docker-compose up -d){Colors.RESET}")
        return
    
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.GREEN}You:{Colors.RESET} ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input == "/quit":
                print(f"{Colors.YELLOW}Goodbye!{Colors.RESET}")
                break
            elif user_input == "/new":
                session = await create_session(agent_name)
                session_id = session["session_id"]
                print(f"{Colors.GREEN}New session: {session_id}{Colors.RESET}\n")
                continue
            
            # Send message
            await send_message(session_id, user_input)
            print()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Goodbye!{Colors.RESET}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}\n")


if __name__ == "__main__":
    agent = sys.argv[1] if len(sys.argv) > 1 else AGENT_NAME
    asyncio.run(chat_loop(agent))
