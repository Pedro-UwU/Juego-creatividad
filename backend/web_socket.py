from fastapi import WebSocket
import logging
from message_handler import handle_message, handle_disconnect

# Configure logging
logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket connection established")

    player_id = None

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"Message received: {data}")

            # Process message with the handler
            player_id = await handle_message(websocket, data, player_id)

    except Exception as e:
        logger.error(f"WebSocket disconnected: {str(e)}")
    finally:
        # Handle disconnection with timeout for reconnection
        if player_id:
            await handle_disconnect(player_id)
