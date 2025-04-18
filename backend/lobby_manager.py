import logging
import json
from enum import Enum
from typing import Dict, List,  Optional

# Configure logging
logger = logging.getLogger(__name__)


class PlayerStatus(Enum):
    WAITING = "WAITING"
    READY = "READY"
    ALIVE = "ALIVE"
    DEAD = "DEAD"


class Player:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.status = PlayerStatus.WAITING

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value
        }


class LobbyManager:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.websockets = {}

    def add_player(self, player_id: str, player_name: str, websocket) -> Player:
        """Add a new player to the lobby."""
        player = Player(player_id, player_name)
        self.players[player_id] = player
        self.websockets[player_id] = websocket
        logger.info(f"Player {player_name} ({player_id}) joined the lobby")
        return player

    def update_player_websocket(self, player_id: str, websocket) -> bool:
        """Update a player's websocket connection (for reconnection)."""
        if player_id not in self.players:
            return False

        self.websockets[player_id] = websocket
        logger.info(f"Updated websocket for player {self.players[player_id].name} ({player_id})")
        return True

    def remove_player(self, player_id: str) -> Optional[Player]:
        """Remove a player from the lobby."""
        player = self.players.pop(player_id, None)
        if player:
            self.websockets.pop(player_id, None)
            logger.info(f"Player {player.name} ({player_id}) left the lobby")
        return player

    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID."""
        return self.players.get(player_id)

    def set_player_status(self, player_id: str, status: PlayerStatus) -> bool:
        """Update a player's status."""
        player = self.get_player(player_id)
        if player:
            player.status = status
            logger.info(f"Player {player.name} ({player_id}) status changed to {status.value}")
            return True
        return False

    def get_players_list(self) -> List[dict]:
        """Get a list of all players."""
        return [player.to_dict() for player in self.players.values()]

    def all_players_ready(self) -> bool:
        """Check if all players are ready."""
        if not self.players:
            return False
        return all(player.status == PlayerStatus.READY for player in self.players.values())

    def start_game(self) -> bool:
        """Start the game by changing all ready players to alive."""
        if not self.all_players_ready():
            return False

        for player in self.players.values():
            if player.status == PlayerStatus.READY:
                player.status = PlayerStatus.ALIVE

        logger.info("Game started!")
        return True

    async def broadcast_lobby_state(self):
        """Send the current lobby state to all connected players."""
        lobby_state = {
            "type": "lobby_state",
            "players": self.get_players_list(),
            "allReady": self.all_players_ready()
        }

        message = json.dumps(lobby_state)

        # Send to all connected players
        for player_id, websocket in list(self.websockets.items()):
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to player {player_id}: {str(e)}")
                # Don't remove here - this will be handled by the disconnect handler


# Create a singleton instance
lobby_manager = LobbyManager()
