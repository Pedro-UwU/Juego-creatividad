import json
import logging
import uuid
import asyncio
from fastapi import WebSocket
from typing import Optional, Callable, Dict, Awaitable 
from lobby_manager import lobby_manager, PlayerStatus

# Configure logging
logger = logging.getLogger(__name__)

# Type definition for message handlers
MessageHandler = Callable[[WebSocket, dict, str], Awaitable[Optional[str]]]

# Dictionary to store disconnected players for potential reconnection
# Format: {player_id: (player_name, removal_task)}
disconnected_players = {}
RECONNECT_TIMEOUT = 60  # seconds to wait before removing disconnected player


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


async def handle_reconnect(websocket: WebSocket, data: dict, _: str) -> Optional[str]:
    """Handle a player reconnecting to the lobby."""
    player_id = data.get("playerId")
    player_name = data.get("playerName", "").strip()

    if not player_id or not player_name:
        await send_error(websocket, "Player ID and name are required for reconnection")
        return None

    # Check if this player is in the disconnected players list
    if player_id in disconnected_players:
        # Cancel the removal task
        removal_task = disconnected_players[player_id][1]
        if removal_task and not removal_task.done():
            removal_task.cancel()

        # Remove from disconnected list
        del disconnected_players[player_id]

        # Check if the player is still in the lobby
        player = lobby_manager.get_player(player_id)
        if player:
            # Update the websocket
            lobby_manager.update_player_websocket(player_id, websocket)

            # Send confirmation to the player
            await websocket.send_text(json.dumps({
                "type": "reconnected"
            }))

            # Broadcast updated lobby state to all players
            await lobby_manager.broadcast_lobby_state()

            logger.info(f"Player {player_name} ({player_id}) reconnected")
            return player_id
        else:
            # Player was already removed, treat as a new connection
            logger.info(f"Player {player_name} reconnection failed - already removed from lobby")

    # If we get here, either:
    # 1. The player wasn't in the disconnected list
    # 2. The player was already removed from the lobby
    # Treat this as a new connection
    return await handle_join(websocket, {"name": player_name}, None)


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


async def handle_ping(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle ping messages to keep the connection alive."""
    await websocket.send_text(json.dumps({
        "type": "pong"
    }))
    return player_id

# Map message types to their handler functions
MESSAGE_HANDLERS: Dict[str, MessageHandler] = {
    "join": handle_join,
    "reconnect": handle_reconnect,
    "ready": handle_ready,
    "unready": handle_unready,
    "start_game": handle_start_game,
    "mark_dead": handle_mark_dead,
    "ping": handle_ping,
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


async def handle_disconnect(player_id: str):
    """Schedule player removal after timeout."""
    if not player_id:
        return

    # Get player before potential removal
    player = lobby_manager.get_player(player_id)
    if not player:
        return

    player_name = player.name

    # Add to disconnected players list
    async def remove_player_after_timeout():
        try:
            await asyncio.sleep(RECONNECT_TIMEOUT)
            # If we reach here, the player didn't reconnect in time
            if player_id in disconnected_players:
                logger.info(f"Removing player {player_name} ({player_id}) after reconnect timeout")
                del disconnected_players[player_id]
                lobby_manager.remove_player(player_id)
                await lobby_manager.broadcast_lobby_state()
        except asyncio.CancelledError:
            # Task was cancelled, which means player reconnected
            logger.info(f"Cancelled removal task for {player_name} ({player_id})")

    # Create and store the removal task
    removal_task = asyncio.create_task(remove_player_after_timeout())
    disconnected_players[player_id] = (player_name, removal_task)

    logger.info(f"Player {player_name} ({player_id}) disconnected, removal scheduled in {RECONNECT_TIMEOUT} seconds")
