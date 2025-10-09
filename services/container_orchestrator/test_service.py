"""
Test script for container orchestrator service.
"""

import asyncio
import httpx
import json
import time
from pathlib import Path


BASE_URL = "http://localhost:8086"


async def test_container_orchestrator():
    """Test container orchestrator endpoints."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        print("=" * 70)
        print("CONTAINER ORCHESTRATOR TEST")
        print("=" * 70)
        
        # 1. Health check
        print("\n1. Health Check")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 2. Execute a simple tool (using alpine:latest for testing)
        print("\n2. Execute Simple Tool (echo)")
        print("-" * 70)
        tool_request = {
            "tool_name": "echo_tool",
            "session_id": "test_session_001",
            "parameters": {"message": "Hello from container!"},
            "image": "alpine:latest",
            "environment": {
                "MESSAGE": "Hello from container!"
            },
            "resource_limits": {
                "memory_mb": 128,
                "cpu_limit": 0.5,
                "timeout_seconds": 30
            },
            "cleanup": True
        }
        
        # Note: This will run alpine container with default command
        # In real usage, tools would have custom entrypoints
        response = await client.post(f"{BASE_URL}/containers/tool/execute", json=tool_request)
        print(f"Status: {response.status_code}")
        result = response.json()
        execution_id = result["execution_id"]
        print(f"Execution ID: {execution_id}")
        print(f"Status: {result['status']}")
        print(f"Exit Code: {result.get('exit_code')}")
        
        # 3. Get execution details
        print("\n3. Get Execution Details")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/containers/tool/{execution_id}")
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Execution: {result['execution_id']}")
        print(f"Status: {result['status']}")
        print(f"Execution time: {result.get('execution_time_seconds', 0):.2f}s")
        
        # 4. Get execution logs
        print("\n4. Get Execution Logs")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/containers/tool/{execution_id}/logs")
        print(f"Status: {response.status_code}")
        logs = response.json()
        print(f"Stdout length: {len(logs.get('stdout', ''))}")
        print(f"Stderr length: {len(logs.get('stderr', ''))}")
        if logs.get('stdout'):
            print(f"Stdout preview: {logs['stdout'][:200]}")
        
        # 5. Start a relic (using nginx as test relic)
        print("\n5. Start Relic (nginx)")
        print("-" * 70)
        relic_request = {
            "relic_name": "test_cache",
            "session_id": "test_session_001",
            "image": "nginx:alpine",
            "resource_limits": {
                "memory_mb": 256,
                "cpu_limit": 1.0,
                "timeout_seconds": 300
            },
            "ports": {
                8080: 80  # Map host:8080 to container:80
            },
            "create_private_network": True,
            "health_check_endpoint": "/",
            "health_check_timeout_seconds": 30
        }
        
        response = await client.post(f"{BASE_URL}/containers/relic/start", json=relic_request)
        print(f"Status: {response.status_code}")
        relic = response.json()
        relic_id = relic["relic_id"]
        print(f"Relic ID: {relic_id}")
        print(f"Container: {relic['container_name']}")
        print(f"Status: {relic['status']}")
        print(f"Healthy: {relic['healthy']}")
        print(f"Internal URL: {relic.get('internal_url')}")
        
        # Wait for relic to be healthy
        print("\nWaiting for relic health check...")
        await asyncio.sleep(3)
        
        # 6. Get relic info
        print("\n6. Get Relic Info")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/containers/relic/{relic_id}")
        print(f"Status: {response.status_code}")
        relic = response.json()
        print(f"Relic: {relic['relic_name']}")
        print(f"Status: {relic['status']}")
        print(f"Healthy: {relic['healthy']}")
        
        # 7. List all relics
        print("\n7. List All Relics")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/containers/relic")
        print(f"Status: {response.status_code}")
        relics = response.json()
        print(f"Found {len(relics)} relics:")
        for r in relics:
            print(f"  - {r['relic_name']} ({r['status']})")
        
        # 8. List relics by session
        print("\n8. List Relics by Session")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/containers/relic?session_id=test_session_001")
        print(f"Status: {response.status_code}")
        relics = response.json()
        print(f"Found {len(relics)} relics for session test_session_001")
        
        # 9. Get container stats
        print("\n9. Get Container Stats")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/containers/stats")
        print(f"Status: {response.status_code}")
        stats = response.json()
        print(f"Found stats for {len(stats)} containers:")
        for s in stats:
            print(f"  - {s['name']}: CPU {s['cpu_percent']:.1f}%, Memory {s['memory_used_mb']:.1f}MB")
        
        # 10. Stop relic
        print("\n10. Stop Relic")
        print("-" * 70)
        response = await client.post(f"{BASE_URL}/containers/relic/{relic_id}/stop")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 11. Cleanup session
        print("\n11. Cleanup Session")
        print("-" * 70)
        cleanup_request = {
            "session_id": "test_session_001",
            "force": True
        }
        response = await client.post(f"{BASE_URL}/containers/cleanup/session", json=cleanup_request)
        print(f"Status: {response.status_code}")
        result = response.json()
        print(f"Containers removed: {result['containers_removed']}")
        print(f"Networks removed: {result['networks_removed']}")
        if result.get('errors'):
            print(f"Errors: {result['errors']}")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_container_orchestrator())
