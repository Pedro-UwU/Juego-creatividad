import { writable } from 'svelte/store';
import { nanoid } from 'nanoid';

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
  return addNotification(`${playerName} has died`, 'death', 3000);
}
