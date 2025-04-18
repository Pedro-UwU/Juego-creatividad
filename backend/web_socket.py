from fastapi import WebSocket
import logging
from message_handler import handle_message
from lobby_manager import lobby_manager

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
        # Clean up when a player disconnects
        if player_id:
            lobby_manager.remove_player(player_id)
            await lobby_manager.broadcast_lobby_state()
