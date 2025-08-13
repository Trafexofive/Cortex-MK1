import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from engine import ChimeraCore
from loader import ResourceLoader
from registries import AgentRegistry
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Chimera Core", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    # Load all agents and tools from the filesystem into registries
    # The path './' is relative to where the container starts, which is /app
    loader = ResourceLoader("./")
    AgentRegistry().load_all(loader)
    logger.info("Chimera Core is awake. Agents have been registered.")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/api/v1/agent/stream")
async def agent_stream(websocket: WebSocket):
    logger.info("Gateway connected to core.")
    await websocket.accept()
    core_engine = ChimeraCore(agent_name="CODENAME: Demurge", session_id="b-line-websocket-session")
    try:
        while True:
            logger.info("Core waiting for message from gateway...")
            data = await websocket.receive_text()
            logger.info(f"Core received from gateway: {data}")
            text_input = data # Simplified for B-Line test

            agent_result = await core_engine.execute_turn(text_input)
            logger.info(f"Core sending to gateway: {agent_result}")
            
            # Send the agent's text response back to the gateway
            await websocket.send_text(json.dumps(agent_result))
    except WebSocketDisconnect:
        logger.info("Gateway disconnected from agent stream.")
    except Exception as e:
        logger.error(f"Error in agent stream: {e}", exc_info=True)
        await websocket.close(code=1011, reason=f"An internal error occurred: {e}")
    finally:
        logger.info("Core connection handler finished.")
