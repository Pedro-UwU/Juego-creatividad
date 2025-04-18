import json
import logging
import uuid
from fastapi import WebSocket
from typing import Optional, Callable, Dict, Awaitable
from lobby_manager import lobby_manager, PlayerStatus

# Configure logging
logger = logging.getLogger(__name__)

# Type definition for message handlers
MessageHandler = Callable[[WebSocket, dict, str], Awaitable[Optional[str]]]


async def send_error(websocket: WebSocket, message: str) -> None:
    """Send an error message to the client."""
    await websocket.send_text(json.dumps({
        "type": "error",
        "message": message
    }))


async def handle_join(websocket: WebSocket, data: dict, _: str) -> Optional[str]:
    """Handle a player joining the lobby."""
    player_name = data.get("name", "").strip()
    if not player_name:
        await send_error(websocket, "Player name is required")
        return None

    # Generate a new player ID
    new_player_id = str(uuid.uuid4())

    # Add player to the lobby
    lobby_manager.add_player(new_player_id, player_name, websocket)

    # Send confirmation to the player
    await websocket.send_text(json.dumps({
        "type": "joined",
        "playerId": new_player_id
    }))

    # Broadcast updated lobby state to all players
    await lobby_manager.broadcast_lobby_state()

    return new_player_id


async def handle_ready(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a player setting ready status."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    lobby_manager.set_player_status(player_id, PlayerStatus.READY)
    await lobby_manager.broadcast_lobby_state()
    return player_id


async def handle_unready(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a player canceling ready status."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    lobby_manager.set_player_status(player_id, PlayerStatus.WAITING)
    await lobby_manager.broadcast_lobby_state()
    return player_id


async def handle_start_game(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a request to start the game."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    if not lobby_manager.all_players_ready():
        await send_error(websocket, "Not all players are ready")
        return player_id

    success = lobby_manager.start_game()
    if success:
        await websocket.send_text(json.dumps({
            "type": "game_started"
        }))
        await lobby_manager.broadcast_lobby_state()
    return player_id


async def handle_mark_dead(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a player marking themselves as dead."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    player = lobby_manager.get_player(player_id)
    if not player or player.status != PlayerStatus.ALIVE:
        await send_error(websocket, "Player is not alive")
        return player_id

    lobby_manager.set_player_status(player_id, PlayerStatus.DEAD)
    await lobby_manager.broadcast_lobby_state()

    # Check if game is over (all players are dead)
    all_dead = all(p.status == PlayerStatus.DEAD for p in lobby_manager.players.values())
    if all_dead:
        await websocket.send_text(json.dumps({
            "type": "game_over"
        }))
    return player_id

# Map message types to their handler functions
MESSAGE_HANDLERS: Dict[str, MessageHandler] = {
    "join": handle_join,
    "ready": handle_ready,
    "unready": handle_unready,
    "start_game": handle_start_game,
    "mark_dead": handle_mark_dead,
}


async def handle_message(websocket: WebSocket, message: str, player_id: str = None) -> Optional[str]:
    """Process incoming WebSocket messages by dispatching to appropriate handlers."""
    try:
        data = json.loads(message)
        message_type = data.get("type")

        # Find the appropriate handler for this message type
        handler = MESSAGE_HANDLERS.get(message_type)
        if handler:
            return await handler(websocket, data, player_id)
        else:
            await send_error(websocket, f"Unknown message type: {message_type}")
            return player_id

    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format: {message}")
        await send_error(websocket, "Invalid message format")
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await send_error(websocket, "Internal server error")

    return player_id
