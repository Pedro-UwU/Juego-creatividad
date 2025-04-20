import { writable } from 'svelte/store';

// Create a store for game state
export const gameState = writable({
  // Connection state
  isConnected: false,
  connectionError: null,
  isReconnecting: false,
  
  // Player information
  playerId: null,
  playerName: '',
  players: [],
  
  // Game state
  allReady: false,
  gameStarted: false,
  gameOver: false,
  gameInProgress: false,
  
  // Role information
  playerRole: null,
  roleInfo: null
});

// Helper functions to update specific parts of the state
export function updateConnectionState(updates) {
  gameState.update(state => ({
    ...state,
    ...updates
  }));
}

export function updatePlayerInfo(updates) {
  gameState.update(state => ({
    ...state,
    ...updates
  }));
}

export function updateGameState(updates) {
  gameState.update(state => ({
    ...state,
    ...updates
  }));
}

export function updateRoleInfo(updates) {
  gameState.update(state => ({
    ...state,
    ...updates
  }));
}

// Reset the entire game state
export function resetGameState() {
  gameState.set({
    isConnected: false,
    connectionError: null,
    isReconnecting: false,
    playerId: null,
    playerName: '',
    players: [],
    allReady: false,
    gameStarted: false,
    gameOver: false,
    gameInProgress: false,
    playerRole: null,
    roleInfo: null
  });
}
