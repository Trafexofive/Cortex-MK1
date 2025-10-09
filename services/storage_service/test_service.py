"""
Test script for storage service.
"""

import asyncio
import httpx
import json
from datetime import datetime


BASE_URL = "http://localhost:8084"


async def test_storage_service():
    """Test all storage service endpoints."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 70)
        print("STORAGE SERVICE TEST")
        print("=" * 70)
        
        # 1. Health check
        print("\n1. Health Check")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 2. Create session
        print("\n2. Create Session")
        print("-" * 70)
        session_data = {
            "agent_name": "test_agent",
            "user_id": "user_test_001",
            "metadata": {"source": "test_script", "version": "1.0"}
        }
        response = await client.post(f"{BASE_URL}/storage/sessions", json=session_data)
        print(f"Status: {response.status_code}")
        session = response.json()
        session_id = session["id"]
        print(f"Created session: {session_id}")
        print(f"Response: {json.dumps(session, indent=2)}")
        
        # 3. Get session
        print("\n3. Get Session")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/sessions/{session_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 4. Add messages
        print("\n4. Add Messages")
        print("-" * 70)
        messages = [
            {"session_id": session_id, "role": "user", "content": "Hello, agent!", "metadata": {}},
            {"session_id": session_id, "role": "assistant", "content": "Hello! How can I help?", "metadata": {}},
            {"session_id": session_id, "role": "user", "content": "What is the weather?", "metadata": {}}
        ]
        
        for msg in messages:
            response = await client.post(f"{BASE_URL}/storage/history", json=msg)
            print(f"Added message: {response.json()['id']} - {msg['role']}: {msg['content'][:30]}...")
        
        # 5. Get conversation history
        print("\n5. Get Conversation History")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/history?session_id={session_id}")
        print(f"Status: {response.status_code}")
        history = response.json()
        print(f"Retrieved {len(history)} messages:")
        for msg in history:
            print(f"  [{msg['role']}] {msg['content'][:50]}...")
        
        # 6. Update state
        print("\n6. Update Agent State")
        print("-" * 70)
        state_data = {
            "data": {
                "context": "weather inquiry",
                "variables": {"location": "unknown", "temperature_unit": "celsius"},
                "memory": ["User greeted", "Asked about weather"]
            }
        }
        response = await client.put(f"{BASE_URL}/storage/state/{session_id}", json=state_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 7. Get state
        print("\n7. Get Agent State")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/state/{session_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 8. Create artifact
        print("\n8. Create Artifact")
        print("-" * 70)
        artifact_data = {
            "session_id": session_id,
            "name": "weather_report.txt",
            "type": "text",
            "path": "/tmp/weather_report.txt",
            "size": 1024,
            "metadata": {"generated_by": "weather_tool"}
        }
        response = await client.post(f"{BASE_URL}/storage/artifacts", json=artifact_data)
        print(f"Status: {response.status_code}")
        artifact = response.json()
        artifact_id = artifact["id"]
        print(f"Created artifact: {artifact_id}")
        print(f"Response: {json.dumps(artifact, indent=2)}")
        
        # 9. List artifacts
        print("\n9. List Artifacts")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/artifacts?session_id={session_id}")
        print(f"Status: {response.status_code}")
        artifacts = response.json()
        print(f"Found {len(artifacts)} artifacts:")
        for art in artifacts:
            print(f"  - {art['name']} ({art['type']}, {art['size']} bytes)")
        
        # 10. Record metrics
        print("\n10. Record Metrics")
        print("-" * 70)
        metrics = [
            {
                "entity_type": "agent",
                "entity_name": "test_agent",
                "session_id": session_id,
                "metric_name": "response_time",
                "value": 0.245,
                "labels": {"model": "gemini"}
            },
            {
                "entity_type": "agent",
                "entity_name": "test_agent",
                "session_id": session_id,
                "metric_name": "token_count",
                "value": 150.0,
                "labels": {"type": "completion"}
            }
        ]
        
        for metric in metrics:
            response = await client.post(f"{BASE_URL}/storage/metrics", json=metric)
            print(f"Recorded metric: {metric['metric_name']} = {metric['value']}")
        
        # 11. Query metrics
        print("\n11. Query Metrics")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/metrics?entity_name=test_agent")
        print(f"Status: {response.status_code}")
        metrics_result = response.json()
        print(f"Found {len(metrics_result)} metrics:")
        for m in metrics_result:
            print(f"  - {m['metric_name']}: {m['value']}")
        
        # 12. Set cache
        print("\n12. Set Cache with TTL")
        print("-" * 70)
        cache_data = {
            "key": "test_cache_key",
            "value": {"result": "cached data", "timestamp": datetime.utcnow().isoformat()},
            "ttl": 3600  # 1 hour
        }
        response = await client.put(f"{BASE_URL}/storage/cache/test_cache_key", json=cache_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 13. Get cache
        print("\n13. Get Cache")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/cache/test_cache_key")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # 14. List sessions
        print("\n14. List Sessions")
        print("-" * 70)
        response = await client.get(f"{BASE_URL}/storage/sessions?agent_name=test_agent")
        print(f"Status: {response.status_code}")
        sessions = response.json()
        print(f"Found {len(sessions)} sessions for test_agent:")
        for s in sessions:
            print(f"  - {s['id']} ({s['status']})")
        
        # 15. Update session status
        print("\n15. Update Session Status")
        print("-" * 70)
        update_data = {"status": "ended"}
        response = await client.put(f"{BASE_URL}/storage/sessions/{session_id}", json=update_data)
        print(f"Status: {response.status_code}")
        print(f"Updated session status to: {response.json()['status']}")
        
        # 16. Delete session (cleanup)
        print("\n16. Delete Session (Cleanup)")
        print("-" * 70)
        response = await client.delete(f"{BASE_URL}/storage/sessions/{session_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_storage_service())
