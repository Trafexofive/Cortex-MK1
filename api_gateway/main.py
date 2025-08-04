from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import httpx
import yaml
import websockets
import asyncio
import json
from .models import InferenceRequest, InferenceResponse
from .transformers import transform_request, transform_response

app = FastAPI(
    title="API Gateway",
    description="A single entry point for all services, with a standardized inference endpoint.",
    version="0.2.0",
)

# Load service configuration
with open("api_gateway/config.yml", "r") as f:
    config = yaml.safe_load(f)
    services = {service["name"]: service for service in config["services"]}

@app.websocket("/v1/inference/stream")
async def unified_inference_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        # The first message should be the InferenceRequest
        initial_data = await websocket.receive_json()
        request = InferenceRequest(**initial_data)

        provider = request.provider
        if provider not in services:
            await websocket.close(code=4000, reason=f"Provider '{provider}' not found.")
            return

        service_config = services[provider]
        upstream_url = service_config.get("upstream_url")
        backend_path_template = service_config.get("inference_path", "/v1/chat/completions")
        backend_path = backend_path_template.format(user_id=request.user_id)
        ws_url = f"{upstream_url.replace('http', 'ws')}{backend_path}"

        async with websockets.connect(ws_url) as upstream_ws:
            # Transform and forward the initial message
            provider_request_data = transform_request(provider, request)
            await upstream_ws.send(json.dumps(provider_request_data))

            # Then, continuously proxy messages
            client_task = asyncio.create_task(websocket.receive_text())
            upstream_task = asyncio.create_task(upstream_ws.receive())

            while True:
                done, pending = await asyncio.wait(
                    [client_task, upstream_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if client_task in done:
                    message = client_task.result()
                    await upstream_ws.send(message)
                    client_task = asyncio.create_task(websocket.receive_text())
                
                if upstream_task in done:
                    message = upstream_task.result()
                    transformed_message = transform_response(provider, json.loads(message))
                    await websocket.send_text(transformed_message.json())
                    upstream_task = asyncio.create_task(upstream_ws.receive())

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        await websocket.close(code=5000, reason=f"An error occurred: {e}")

@app.post("/v1/inference")
async def unified_inference(request: InferenceRequest):
    """
    Provides a standardized inference endpoint that routes requests to the
    appropriate backend service based on the 'provider' field.
    """
    provider = request.provider
    if provider not in services:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found.")

    service_config = services[provider]
    upstream_url = service_config.get("upstream_url")

    provider_request_data = transform_request(provider, request)

    async with httpx.AsyncClient() as client:
        try:
            backend_path_template = service_config.get("inference_path", "/v1/chat/completions")
            backend_path = backend_path_template.format(user_id=request.user_id)
            url = f"{upstream_url}{backend_path}"
            
            response = await client.post(url, json=provider_request_data)
            response.raise_for_status()
            
            provider_response_data = response.json()
            
            return transform_response(provider, provider_response_data)

        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service '{provider}' is unavailable: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
