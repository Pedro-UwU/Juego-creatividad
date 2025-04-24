import json
import logging
import uuid
import asyncio
from fastapi import WebSocket
from typing import Optional, Callable, Dict, Awaitable
from lobby_manager import lobby_manager, PlayerStatus
from game_roles import Role

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
    player = lobby_manager.add_player(new_player_id, player_name, websocket)

    # Check if game is in progress (cannot join)
    if not player:
        await send_error(websocket, "Cannot join - game is already in progress")
        return None

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
    game_id = data.get("gameId")

    if not player_id or not player_name:
        await send_error(websocket, "Player ID and name are required for reconnection")
        return None

    # Check if game ID matches current game
    if game_id and game_id != lobby_manager.game_id:
        logger.info(
            f"Player {player_name} tried to reconnect to a different game session")
        await websocket.send_text(json.dumps({
            "type": "game_id_mismatch",
            "currentGameId": lobby_manager.game_id
        }))
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
            logger.info(
                f"Player {player_name} reconnection failed - already removed from lobby")

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

    # Only allow unready if game hasn't started
    if lobby_manager.game_in_progress:
        await send_error(websocket, "Cannot change ready status - game in progress")
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

    # Check minimum player count
    if len(lobby_manager.players) < 2:
        await send_error(websocket, "Need at least 2 players to start")
        return player_id

    try:
        success = lobby_manager.start_game()
        if success:
            # First broadcast updated lobby state with roles
            await lobby_manager.broadcast_lobby_state()

            # Then notify all players that the game has started
            for pid, ws in lobby_manager.websockets.items():
                try:
                    await ws.send_text(json.dumps({
                        "type": "game_started"
                    }))
                except Exception as e:
                    logger.error(f"Error sending game_started to player {
                                 pid}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in handle_start_game: {str(e)}")
        await send_error(websocket, "Error starting game")

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

    # Special rule: Doctor cannot die unless all other players are dead
    if player.role == Role.DOCTOR and not lobby_manager.can_doctor_die():
        await send_error(websocket, "The Doctor cannot die until all other players are dead")
        return player_id

    lobby_manager.set_player_status(player_id, PlayerStatus.DEAD)
    await lobby_manager.broadcast_lobby_state()

    # Check if game is over (half or more non-doctor players are dead)
    if lobby_manager.should_game_end():
        # End the current game and get winner
        winner = lobby_manager.end_game()

        # Notify all players
        for ws in lobby_manager.websockets.values():
            try:
                await ws.send_text(json.dumps({
                    "type": "game_over",
                    "winner": winner
                }))
            except Exception as e:
                logger.error(f"Error sending game_over: {str(e)}")

        # Broadcast the updated lobby state with new game ID
        await lobby_manager.broadcast_lobby_state()

    return player_id


async def handle_end_game(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a doctor requesting to end the game."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    player = lobby_manager.get_player(player_id)
    if not player or player.status != PlayerStatus.ALIVE:
        await send_error(websocket, "Player is not alive")
        return player_id

    # Only the doctor can end the game
    if player.role != Role.DOCTOR:
        await send_error(websocket, "Only the Doctor can end the game")
        return player_id

    # End the current game
    winner = lobby_manager.end_game()

    # Notify all players
    for ws in lobby_manager.websockets.values():
        try:
            await ws.send_text(json.dumps({
                "type": "game_over",
                "endedByDoctor": True,
                "winner": winner
            }))
        except Exception as e:
            logger.error(f"Error sending game_over: {str(e)}")

    # Broadcast the updated lobby state with new game ID
    await lobby_manager.broadcast_lobby_state()

    return player_id


async def handle_start_round(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a doctor request to start a new round."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    player = lobby_manager.get_player(player_id)
    if not player or player.status != PlayerStatus.ALIVE:
        await send_error(websocket, "Player is not alive")
        return player_id

    # Only the doctor can start a round
    if player.role != Role.DOCTOR:
        await send_error(websocket, "Only the Doctor can start a round")
        return player_id

    # Start a new round
    success = lobby_manager.start_new_round()
    if not success:
        await send_error(websocket, "Failed to start round")
        return player_id

    # Notify all players that a round has started
    for ws in lobby_manager.websockets.values():
        try:
            await ws.send_text(json.dumps({
                "type": "round_started",
                "roundNumber": lobby_manager.current_round
            }))
        except Exception as e:
            logger.error(f"Error sending round_started: {str(e)}")

    # Send the list of sick players to the doctor
    sick_players_info = []
    for sick_id in lobby_manager.sick_players:
        sick_player = lobby_manager.get_player(sick_id)
        if sick_player:
            sick_players_info.append({
                "id": sick_player.id,
                "name": sick_player.name
            })

    await websocket.send_text(json.dumps({
        "type": "sick_players",
        "players": sick_players_info
    }))

    # Broadcast updated lobby state to all players
    await lobby_manager.broadcast_lobby_state()

    return player_id


async def handle_cure_player(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a doctor curing a sick player."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    player = lobby_manager.get_player(player_id)
    if not player or player.status != PlayerStatus.ALIVE:
        await send_error(websocket, "Player is not alive")
        return player_id

    # Only the doctor can cure a player
    if player.role != Role.DOCTOR:
        await send_error(websocket, "Only the Doctor can cure a player")
        return player_id

    # Get the player to cure
    player_to_cure_id = data.get("playerId")

    # Doctor may choose not to cure anyone
    if player_to_cure_id:
        # Apply the cure
        success = lobby_manager.cure_player(player_to_cure_id)
        if not success:
            await send_error(websocket, "Failed to cure player")
            return player_id

        # Get the player name for the response
        cured_player = lobby_manager.get_player(player_to_cure_id)
        player_name = cured_player.name if cured_player else "Unknown player"

        # Notify the doctor of the cure action
        await websocket.send_text(json.dumps({
            "type": "player_cured",
            "playerId": player_to_cure_id,
            "playerName": player_name
        }))
    else:
        # Doctor chose not to cure anyone
        lobby_manager.cured_player = None
        await websocket.send_text(json.dumps({
            "type": "no_player_cured"
        }))

    return player_id


async def handle_end_round(websocket: WebSocket, data: dict, player_id: str) -> Optional[str]:
    """Handle a doctor ending the current round."""
    if not player_id:
        await send_error(websocket, "Not connected to a lobby")
        return player_id

    player = lobby_manager.get_player(player_id)
    if not player or player.status != PlayerStatus.ALIVE:
        await send_error(websocket, "Player is not alive")
        return player_id

    # Only the doctor can end a round
    if player.role != Role.DOCTOR:
        await send_error(websocket, "Only the Doctor can end a round")
        return player_id

    # End the round
    result = lobby_manager.end_round()

    # If game ended, result will be the winning team
    if isinstance(result, str):
        # Game is over, result contains the winner
        for ws in lobby_manager.websockets.values():
            try:
                await ws.send_text(json.dumps({
                    "type": "game_over",
                    "winner": result
                }))
            except Exception as e:
                logger.error(f"Error sending game_over: {str(e)}")
    else:
        # Round ended normally, notify all players
        for ws in lobby_manager.websockets.values():
            try:
                await ws.send_text(json.dumps({
                    "type": "round_ended",
                    "roundNumber": lobby_manager.current_round
                }))
            except Exception as e:
                logger.error(f"Error sending round_ended: {str(e)}")

    # Broadcast updated lobby state to all players
    await lobby_manager.broadcast_lobby_state()

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
    "end_game": handle_end_game,
    "start_round": handle_start_round,  # New handler
    "cure_player": handle_cure_player,  # New handler
    "end_round": handle_end_round,      # New handler
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
                logger.info(f"Removing player {player_name} ({
                            player_id}) after reconnect timeout")
                del disconnected_players[player_id]
                lobby_manager.remove_player(player_id)
                await lobby_manager.broadcast_lobby_state()
        except asyncio.CancelledError:
            # Task was cancelled, which means player reconnected
            logger.info(f"Cancelled removal task for {
                        player_name} ({player_id})")

    # Create and store the removal task
    removal_task = asyncio.create_task(remove_player_after_timeout())
    disconnected_players[player_id] = (player_name, removal_task)

    logger.info(f"Player {player_name} ({player_id}) disconnected, removal scheduled in {
                RECONNECT_TIMEOUT} seconds")
