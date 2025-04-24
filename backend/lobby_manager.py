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
    SICK = "SICK"  # New status for players who are sick in a round
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

        # Add status color for UI display
        status_colors = {
            PlayerStatus.SICK: "#6B8E23"  # Olive green/slimy color for sick players
        }

        if self.status in status_colors:
            base_dict["statusColor"] = status_colors[self.status]

        return base_dict


class LobbyManager:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.websockets = {}
        self.game_in_progress = False
        # Generate a unique ID for this game session
        self.game_id = str(uuid.uuid4())
        self.current_round = 0
        self.sick_players: List[str] = []  # List of player IDs who are currently sick
        self.cured_player: Optional[str] = None  # ID of player cured in current round

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

    def start_new_round(self) -> bool:
        """Start a new round by randomly selecting players to get sick."""
        if not self.game_in_progress:
            logger.error("Cannot start round - game not in progress")
            return False

        # Reset round state
        self.current_round += 1
        self.sick_players = []
        self.cured_player = None

        logger.info(f"Starting round {self.current_round}")

        # Get all alive players except the doctor
        alive_players = [
            player for player in self.players.values()
            if player.status == PlayerStatus.ALIVE and player.role != Role.DOCTOR
        ]

        # Determine how many players should get sick
        num_to_sicken = 1  # Default
        if len(self.players) > 10:
            num_to_sicken = 2

        # Cap at 4 or the number of alive non-doctor players, whichever is smaller
        num_to_sicken = min(num_to_sicken, 4, len(alive_players))

        if num_to_sicken == 0:
            logger.warning("No players to make sick - skipping round")
            return False

        # Randomly select players to get sick
        sick_candidates = random.sample(alive_players, num_to_sicken)

        # Mark selected players as sick
        for player in sick_candidates:
            player.status = PlayerStatus.SICK
            self.sick_players.append(player.id)
            logger.info(f"Player {player.name} ({player.id}) is now sick")

        return True

    def cure_player(self, player_id: str) -> bool:
        """Doctor cures a sick player."""
        if not self.game_in_progress or not self.sick_players:
            return False

        # Verify the player is sick
        player = self.get_player(player_id)
        if not player or player.status != PlayerStatus.SICK:
            return False

        # Record the cured player
        self.cured_player = player_id
        logger.info(f"Player {player.name} ({player_id}) has been cured")

        return True

    def end_round(self) -> bool:
        """End the current round, causing uncured sick players to die."""
        if not self.game_in_progress:
            return False

        logger.info(f"Ending round {self.current_round}")

        # Process sick players
        for player_id in self.sick_players:
            # Skip the cured player
            if player_id == self.cured_player:
                # Restore cured player to ALIVE status
                player = self.get_player(player_id)
                if player:
                    player.status = PlayerStatus.ALIVE
                    logger.info(f"Player {player.name} ({player_id}) has recovered")
                continue

            # Uncured sick players die
            player = self.get_player(player_id)
            if player:
                player.status = PlayerStatus.DEAD
                logger.info(f"Player {player.name} ({player_id}) has died from sickness")

        # Check if game should end (half or more non-doctor players are dead)
        if self.should_game_end():
            return self.end_game()

        # Reset sick players list for next round
        self.sick_players = []
        self.cured_player = None

        return True

    def should_game_end(self) -> bool:
        """Check if the game should end (half or more non-doctor players are dead)."""
        non_doctor_players = [p for p in self.players.values() if p.role != Role.DOCTOR]
        dead_players = [p for p in non_doctor_players if p.status == PlayerStatus.DEAD]

        return len(dead_players) >= len(non_doctor_players) / 2

    def calculate_winner(self) -> str:
        """Calculate which team won the game (ALLY or ENEMY)."""
        team_counts = RoleAssigner.count_alive_team_members(self.players.values())

        # Check if allies outnumber enemies
        if team_counts["ALLY"] > team_counts["ENEMY"]:
            return "ALLY"
        else:
            return "ENEMY"

    def end_game(self) -> bool:
        """End the current game and reset for a new one."""
        if not self.game_in_progress:
            return False

        # Calculate the winner before resetting
        winner = self.calculate_winner()
        logger.info(f"Game over! Winner: {winner}")

        # Generate a new game ID for the next game
        self.game_id = str(uuid.uuid4())

        # Reset game state
        self.game_in_progress = False
        self.current_round = 0
        self.sick_players = []
        self.cured_player = None

        # Reset player statuses (keeping them in the lobby)
        for player in self.players.values():
            player.status = PlayerStatus.WAITING
            player.role = None

        logger.info(f"Game ended. New lobby ID: {self.game_id}")
        return winner


# Create a singleton instance
lobby_manager = LobbyManager()
