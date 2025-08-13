import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import websockets
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Cortex-Prime API Gateway", version="0.1.0")
CHIMERA_CORE_WS_URL = "ws://chimera_core:8001/api/v1/agent/stream"
VOICE_SERVICE_WS_URL = "ws://voice_service:8002/ws/transcribe"

@app.get("/health")
async def health_check():
    return {"status": "gateway_ok"}

@app.websocket("/v1/inference/stream")
async def inference_stream_proxy(client_ws: WebSocket):
    logger.info("Client connected to gateway.")
    await client_ws.accept()
    try:
        logger.info("Connecting to core websocket...")
        async with websockets.connect(CHIMERA_CORE_WS_URL) as upstream_ws:
            logger.info("Gateway connected to Chimera Core WebSocket.")

            async def forward_to_upstream():
                while True:
                    logger.info("Waiting for message from client...")
                    data = await client_ws.receive_text()
                    logger.info(f"Received from client: {data}")
                    await upstream_ws.send(data)
                    logger.info("Sent to core.")

            async def forward_to_client():
                while True:
                    logger.info("Waiting for message from core...")
                    response = await upstream_ws.recv()
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
