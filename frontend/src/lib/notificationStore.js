import { writable } from 'svelte/store';
import { nanoid } from 'nanoid';
import { getText } from './textStore.js';

// Store for notifications
export const notifications = writable([]);

// Add a new notification
export function addNotification(message, type = 'info', duration = 3000) {
  const id = nanoid();
  
  // Add notification to the store
  notifications.update(all => [
    ...all,
    { id, message, type, duration }
  ]);
  
  // Auto-remove after duration + animation time
  setTimeout(() => {
    removeNotification(id);
  }, duration + 500);
  
  return id;
}

// Remove a notification by id
export function removeNotification(id) {
  notifications.update(all => all.filter(n => n.id !== id));
}

// Create a death notification
export function notifyPlayerDeath(playerName) {
  return addNotification(
    getText('notifications.player_death', { playerName }), 
    'death', 
    3000
  );
}

// Create a sick notification
export function notifyPlayerSick(playerName) {
  return addNotification(
    getText('notifications.player_sick', { playerName }), 
    'sick', 
    3000
  );
}

// Create a player cured notification
export function notifyPlayerCured(playerName) {
  return addNotification(
    getText('notifications.player_cured', { playerName }), 
    'cure', 
    3000
  );
}

// Create a round started notification
export function notifyRoundStarted(roundNumber) {
  return addNotification(
    getText('notifications.round_started', { roundNumber }), 
    'round', 
    3000
  );
}

// Create a round ended notification
export function notifyRoundEnded(roundNumber) {
  return addNotification(
    getText('notifications.round_ended', { roundNumber }), 
    'round', 
    3000
  );
}

// Create a game over notification
export function notifyGameOver(winner) {
  return addNotification(
    getText('notifications.game_over', { winner }), 
    'gameOver', 
    5000
  );
}
