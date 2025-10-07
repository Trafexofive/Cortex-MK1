import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from httpx_ws import aconnect_ws
import httpx
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Cortex-Prime API Gateway", version="0.1.0")

# Service URLs
CHIMERA_CORE_URL = "http://chimera_core:8001"
CHIMERA_CORE_WS_URL = "ws://chimera_core:8001/api/v1/agent/stream"
VOICE_SERVICE_WS_URL = "ws://voice_service:8002/ws/transcribe"

# HTTP client for REST API calls
http_client = httpx.AsyncClient()

@app.get("/health")
async def health_check():
    return {"status": "gateway_ok"}

# REST API endpoints - proxy to Chimera Core
@app.get("/v1/agent/health")
async def agent_health():
    try:
        response = await http_client.get(f"{CHIMERA_CORE_URL}/health")
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error calling Chimera Core health endpoint: {e}")
        raise HTTPException(status_code=503, detail=f"Chimera Core unavailable: {e}")

@app.post("/v1/agent/prompt")
async def agent_prompt(prompt_data: dict):
    try:
        response = await http_client.post(f"{CHIMERA_CORE_URL}/api/v1/agent/prompt", json=prompt_data)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error calling Chimera Core prompt endpoint: {e}")
        raise HTTPException(status_code=503, detail=f"Chimera Core unavailable: {e}")

@app.get("/system/registries/agents")
async def get_agents():
    try:
        response = await http_client.get(f"{CHIMERA_CORE_URL}/system/registries/agents")
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error calling Chimera Core agents registry endpoint: {e}")
        raise HTTPException(status_code=503, detail=f"Chimera Core unavailable: {e}")

@app.get("/system/registries/tools")
async def get_tools():
    try:
        response = await http_client.get(f"{CHIMERA_CORE_URL}/system/registries/tools")
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error calling Chimera Core tools registry endpoint: {e}")
        raise HTTPException(status_code=503, detail=f"Chimera Core unavailable: {e}")

@app.get("/system/registries/relics")
async def get_relics():
    try:
        response = await http_client.get(f"{CHIMERA_CORE_URL}/system/registries/relics")
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as e:
        logger.error(f"Error calling Chimera Core relics registry endpoint: {e}")
        raise HTTPException(status_code=503, detail=f"Chimera Core unavailable: {e}")

# WebSocket endpoints
@app.websocket("/v1/inference/stream")
async def inference_stream_proxy(client_ws: WebSocket):
    logger.info("Client connected to gateway.")
    await client_ws.accept()
    try:
        logger.info("Connecting to core websocket...")
        async with aconnect_ws(CHIMERA_CORE_WS_URL) as upstream_ws:
            logger.info("Gateway connected to Chimera Core WebSocket.")

            async def forward_to_upstream():
                while True:
                    data = await client_ws.receive_text()
                    logger.info(f"Received from client: {data}")
                    await upstream_ws.send_text(data)
                    logger.info("Sent to core.")

            async def forward_to_client():
                while True:
                    response = await upstream_ws.receive_text()
                    logger.info(f"Received from core: {response}")
                    await client_ws.send_text(response)
                    logger.info("Sent to client.")

            await asyncio.gather(forward_to_upstream(), forward_to_client())

    except WebSocketDisconnect:
        logger.info("Client disconnected from gateway.")
    except Exception as e:
        logger.error(f"Gateway proxy error: {e}", exc_info=True)
        await client_ws.close(code=1011, reason=f"Gateway error: {e}")
    finally:
        logger.info("Gateway connection handler finished.")

@app.websocket("/v1/voice/stream")
async def voice_stream_proxy(client_ws: WebSocket):
    logger.info("Client connected to voice gateway.")
    await client_ws.accept()
    try:
        logger.info("Connecting to voice service websocket...")
        async with websockets.connect(VOICE_SERVICE_WS_URL) as upstream_ws:
            logger.info("Gateway connected to Voice Service WebSocket.")

            async def forward_to_upstream():
                while True:
                    logger.info("Waiting for audio message from client...")
                    data = await client_ws.receive_bytes()
                    logger.info(f"Received from client: {len(data)} bytes")
                    await upstream_ws.send(data)
                    logger.info("Sent to voice service.")

            async def forward_to_client():
                while True:
                    logger.info("Waiting for transcription from voice service...")
                    response = await upstream_ws.recv()
                    logger.info(f"Received from voice service: {response}")
                    await client_ws.send_text(response)
                    logger.info("Sent transcription to client.")

            await asyncio.gather(forward_to_upstream(), forward_to_client())

    except WebSocketDisconnect:
        logger.info("Client disconnected from voice gateway.")
    except Exception as e:
        logger.error(f"Gateway voice proxy error: {e}", exc_info=True)
        await client_ws.close(code=1011, reason=f"Gateway error: {e}")
    finally:
        logger.info("Gateway voice connection handler finished.")