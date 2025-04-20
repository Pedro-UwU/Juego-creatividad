import logging
import json
import uuid
import asyncio
from enum import Enum
from typing import Dict, List, Optional
from game_roles import Role, RoleAssigner

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
        self.role = None  # Will be assigned when game starts

    def to_dict(self):
        base_dict = {
            "id": self.id,
            "name": self.name,
            "status": self.status.value
        }

        # Add role information if assigned
        if self.role:
            base_dict["role"] = self.role.value

        return base_dict

    def get_private_dict(self):
        """Get a dictionary with private player info (including detailed role)."""
        base_dict = self.to_dict()

        # Add detailed role information if assigned
        if self.role:
            base_dict.update(RoleAssigner.get_role_info(self.role))

        return base_dict


class LobbyManager:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.websockets = {}
        self.game_in_progress = False
        # Generate a unique ID for this game session
        self.game_id = str(uuid.uuid4())

    def add_player(self, player_id: str, player_name: str, websocket) -> Player:
        """Add a new player to the lobby."""
        # Don't allow new players if game is in progress
        if self.game_in_progress:
            return None

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
        logger.info(f"Updated websocket for player {
                    self.players[player_id].name} ({player_id})")
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
            logger.info(f"Player {player.name} ({
                        player_id}) status changed to {status.value}")
            return True
        return False

    def get_players_list(self) -> List[dict]:
        """Get a list of all players (with public information)."""
        return [player.to_dict() for player in self.players.values()]

    def all_players_ready(self) -> bool:
        """Check if all players are ready."""
        if not self.players:
            return False
        return all(player.status == PlayerStatus.READY for player in self.players.values())

    def assign_roles(self) -> Dict[str, Role]:
        """Assign roles to all players in the lobby."""
        num_players = len(self.players)

        # Get a list of roles
        roles = RoleAssigner.assign_roles(num_players)

        # Assign roles to players
        players_list = list(self.players.values())
        role_assignments = {}

        for i, player in enumerate(players_list):
            if i < len(roles):
                player.role = roles[i]
                role_assignments[player.id] = roles[i]
                logger.info(f"Assigned role {
                            roles[i].value} to player {player.name}")

        return role_assignments

    def start_game(self) -> bool:
        """Start the game by assigning roles and changing all ready players to alive."""
        if not self.all_players_ready() or len(self.players) < 2:
            return False

        # Assign roles
        role_assignments = self.assign_roles()

        # Change status to ALIVE
        for player in self.players.values():
            if player.status == PlayerStatus.READY:
                player.status = PlayerStatus.ALIVE

        # Set game in progress
        self.game_in_progress = True

        logger.info(f"Game started with ID: {self.game_id}!")
        return True

    def end_game(self) -> bool:
        """End the current game and reset for a new one."""
        if not self.game_in_progress:
            return False

        # Generate a new game ID for the next game
        self.game_id = str(uuid.uuid4())

        # Reset game state
        self.game_in_progress = False

        # Reset player statuses (keeping them in the lobby)
        for player in self.players.values():
            player.status = PlayerStatus.WAITING
            player.role = None

        logger.info(f"Game ended. New lobby ID: {self.game_id}")
        return True

    def can_doctor_die(self) -> bool:
        """Check if the doctor can be marked as dead (only if all other players are dead)."""
        non_doctor_alive = False

        for player in self.players.values():
            if player.role != Role.DOCTOR and player.status == PlayerStatus.ALIVE:
                non_doctor_alive = True
                break

        return not non_doctor_alive

    def is_game_over(self) -> bool:
        """Check if the game is over (all players are dead)."""
        return all(player.status != PlayerStatus.ALIVE for player in self.players.values())

    def reset_game(self):
        """Reset the game state for a new game."""
        self.players = {}
        self.websockets = {}
        self.game_in_progress = False
        self.game_id = str(uuid.uuid4())
        logger.info(f"Game reset. New game ID: {self.game_id}")

    async def broadcast_lobby_state(self):
        """Send the current lobby state to all connected players."""
        # Public information for all players
        lobby_state = {
            "type": "lobby_state",
            "players": self.get_players_list(),
            "allReady": self.all_players_ready(),
            "gameInProgress": self.game_in_progress,
            "gameId": self.game_id
        }

        public_message = json.dumps(lobby_state)

        # Send to all connected players
        for player_id, websocket in list(self.websockets.items()):
            try:
                # First send the public state
                await websocket.send_text(public_message)

                # Add a small delay to prevent overwhelming the connection
                await asyncio.sleep(0.05)

                # Then, if game in progress, send private player info
                if self.game_in_progress:
                    player = self.players.get(player_id)
                    if player and player.role:
                        try:
                            private_message = json.dumps({
                                "type": "player_role",
                                "player": player.get_private_dict()
                            })
                            await websocket.send_text(private_message)
                        except Exception as e:
                            logger.error(f"Error sending role info to player {
                                         player_id}: {str(e)}")

            except Exception as e:
                logger.error(f"Error sending message to player {
                             player_id}: {str(e)}")
                # Don't remove here - this will be handled by the disconnect handler


# Create a singleton instance
lobby_manager = LobbyManager()
