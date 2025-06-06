import random
from enum import Enum
from typing import List, Dict
import logging

# Configure logging
logger = logging.getLogger(__name__)


class Role(Enum):
    DOCTOR = "DOCTOR"
    ALLY = "ALLY"
    ENEMY = "ENEMY"
    HEARTBROKEN_ALLY = "HEARTBROKEN_ALLY"
    HEARTBROKEN_ENEMY = "HEARTBROKEN_ENEMY"


class RoleAssigner:
    @staticmethod
    def assign_roles(num_players: int) -> List[Role]:
        """
        Assign roles to players based on the number of players in the game.

        Rules:
        - Exactly one doctor
        - At most one heartbroken (can be ally or enemy)
        - Remaining players split between allies and enemies

        Returns a shuffled list of roles.
        """
        if num_players < 2:
            logger.error("Cannot assign roles for fewer than 2 players")
            return [Role.ALLY] * num_players  # Fallback

        roles = [Role.DOCTOR]  # Always have one doctor

        # Decide if we should have a heartbroken player
        # 70% chance if enough players
        has_heartbroken = random.random() < 0.7 and num_players >= 3

        # Calculate number of enemies (roughly 1/3 of remaining players, minimum 1)
        remaining = num_players - 1  # subtract doctor
        if has_heartbroken:
            remaining -= 1  # subtract heartbroken

        num_enemies = max(1, round(remaining / 3))
        num_allies = remaining - num_enemies

        # Add regular roles
        roles.extend([Role.ALLY] * num_allies)
        roles.extend([Role.ENEMY] * num_enemies)

        # Add heartbroken if needed
        if has_heartbroken:
            # Decide if heartbroken is ally or enemy (50% chance either way)
            heartbroken_role = Role.HEARTBROKEN_ALLY if random.random() < 0.5 else Role.HEARTBROKEN_ENEMY
            roles.append(heartbroken_role)

        # Shuffle the roles
        random.shuffle(roles)

        logger.info(f"Assigned roles: {[r.value for r in roles]}")
        return roles

    @staticmethod
    def get_base_role(role: Role) -> Role:
        """Get the base role (ALLY or ENEMY) for a given role."""
        if role in [Role.ALLY, Role.HEARTBROKEN_ALLY]:
            return Role.ALLY
        elif role in [Role.ENEMY, Role.HEARTBROKEN_ENEMY]:
            return Role.ENEMY
        return role  # DOCTOR remains as is

    @staticmethod
    def is_heartbroken(role: Role) -> bool:
        """Check if a role is a heartbroken variant."""
        return role in [Role.HEARTBROKEN_ALLY, Role.HEARTBROKEN_ENEMY]

    @staticmethod
    def get_role_info(role: Role) -> Dict[str, any]:
        """Get information about a role for the client."""
        is_heartbroken = RoleAssigner.is_heartbroken(role)
        base_role = RoleAssigner.get_base_role(role)

        role_colors = {
            Role.DOCTOR: "#4CAF50",  # Green
            Role.ALLY: "#2196F3",    # Blue
            Role.ENEMY: "#F44336"    # Red
        }

        return {
            "role": role.value,
            "baseRole": base_role.value,
            "isHeartbroken": is_heartbroken,
            # Default gray if somehow invalid
            "color": role_colors.get(base_role, "#9E9E9E")
        }

    @staticmethod
    def count_team_members(players: List, team_role: Role = None) -> Dict[str, int]:
        """Count players on each team (ally vs enemy).

        If team_role is specified, only returns the count for that team.
        Otherwise returns a dictionary with counts for both teams.
        """
        ally_count = 0
        enemy_count = 0

        for player in players:
            if not hasattr(player, 'role') or not player.role:
                continue

            base_role = RoleAssigner.get_base_role(player.role)
            if base_role == Role.ALLY:
                ally_count += 1
            elif base_role == Role.ENEMY:
                enemy_count += 1

        # If a specific team was requested, return just that count
        if team_role == Role.ALLY:
            return ally_count
        elif team_role == Role.ENEMY:
            return enemy_count

        # Otherwise return counts for both teams
        return {
            "ALLY": ally_count,
            "ENEMY": enemy_count
        }

    @staticmethod
    def count_alive_team_members(players: List, team_role: Role = None) -> Dict[str, int]:
        """Count alive players on each team.

        Similar to count_team_members but only counts alive players.
        """
        from lobby_manager import PlayerStatus  # Import here to avoid circular imports

        ally_count = 0
        enemy_count = 0

        for player in players:
            if not hasattr(player, 'role') or not player.role:
                continue

            # Only count alive players
            if not hasattr(player, 'status') or player.status not in [PlayerStatus.ALIVE, PlayerStatus.SICK]:
                continue

            base_role = RoleAssigner.get_base_role(player.role)
            if base_role == Role.ALLY:
                ally_count += 1
            elif base_role == Role.ENEMY:
                enemy_count += 1

        # If a specific team was requested, return just that count
        if team_role == Role.ALLY:
            return ally_count
        elif team_role == Role.ENEMY:
            return enemy_count

        # Otherwise return counts for both teams
        return {
            "ALLY": ally_count,
            "ENEMY": enemy_count
        }
