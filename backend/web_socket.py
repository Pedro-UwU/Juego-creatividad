from fastapi import WebSocket
import logging

# Configure logging
logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket connection established")
    try:
        while True:
            # Receive and echo back messages
            data = await websocket.receive_text()
            logger.info(f"Message received: {data}")
            await websocket.send_text(f"Message received: {data}")
    except Exception as e:
        logger.error(f"WebSocket disconnected: {str(e)}")
