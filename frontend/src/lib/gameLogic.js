import { sendMessage } from './websocketService.js';
import { getText } from './textStore.js';

// Game action functions
export function setReady() {
  console.log('Setting player status to READY');
  return sendMessage({
    type: 'ready'
  });
}

export function setUnready() {
  console.log('Setting player status to WAITING');
  return sendMessage({
    type: 'unready'
  });
}

export function startGame() {
  console.log('Starting game');
  return sendMessage({
    type: 'start_game'
  });
}

export function markAsDead() {
  console.log('Marking player as dead');
  return sendMessage({
    type: 'mark_dead'
  });
}

export function endGame() {
  console.log('Doctor is ending the game');
  return sendMessage({
    type: 'end_game'
  });
}

// Get role display text
export function getRoleDisplayText(role) {
  if (!role) return '';
  
  const roleLower = role.toLowerCase();
  
  switch (roleLower) {
    case 'doctor':
      return getText('roles.doctor');
    case 'ally':
      return getText('roles.ally');
    case 'enemy':
      return getText('roles.enemy');
    case 'heartbroken_ally':
      return getText('roles.heartbroken_ally');
    case 'heartbroken_enemy':
      return getText('roles.heartbroken_enemy');
    default:
      return role;
  }
}

// Get role description text
export function getRoleDescription(role) {
  if (!role) return '';
  
  const roleLower = role.toLowerCase();
  
  switch (roleLower) {
    case 'doctor':
      return getText('roles.description.doctor');
    case 'ally':
      return getText('roles.description.ally');
    case 'enemy':
      return getText('roles.description.enemy');
    case 'heartbroken_ally':
      return getText('roles.description.heartbroken_ally');
    case 'heartbroken_enemy':
      return getText('roles.description.heartbroken_enemy');
    default:
      return '';
  }
}

// Get a CSS class based on the player's status
export function getStatusClass(status) {
  switch (status) {
    case 'WAITING': return 'status-waiting';
    case 'READY': return 'status-ready';
    case 'ALIVE': return 'status-alive';
    case 'DEAD': return 'status-dead';
    default: return '';
  }
}

// Check if the current player can mark themselves as dead
export function canMarkAsDead(playerRole, playerStatus) {
  // Only alive players can mark themselves as dead
  if (playerStatus !== 'ALIVE') {
    return false;
  }
  
  // The doctor has special rules - this is handled on the server side
  return true;
}

// Handle any custom game-specific messages
export function handleGameMessage(data) {
  // This function can be expanded for any custom game-specific messages
  console.log('Received game-specific message:', data);
  
  // No custom messages implemented yet
}

// Check if all players in the current team are dead
export function isTeamDead(players, team) {
  if (!players || !players.length) return false;
  
  return players
    .filter(player => getTeam(player.role) === team)
    .every(player => player.status === 'DEAD');
}

// Determine a player's team based on their role
export function getTeam(role) {
  if (!role) return null;
  
  const roleLower = role.toLowerCase();
  
  if (roleLower === 'doctor' || 
      roleLower === 'ally' || 
      roleLower === 'heartbroken_ally') {
    return 'ALLY';
  }
  
  if (roleLower === 'enemy' || 
      roleLower === 'heartbroken_enemy') {
    return 'ENEMY';
  }
  
  return null;
}
