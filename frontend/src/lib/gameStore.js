import { writable } from 'svelte/store';
import { getText } from './textStore.js';

// Create a store for game state
export const gameState = writable({
  isConnected: false,
  connectionError: null,
  isReconnecting: false,
  playerId: null,
  playerName: '',
  players: [],
  allReady: false,
  gameStarted: false,
  gameOver: false
});

// Socket instance
let socket = null;

// Reconnection variables
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectInterval = 3000; // 3 seconds between reconnect attempts
let reconnectTimer = null;
let isIntentionalDisconnect = false;
let pingInterval = null;
const PING_INTERVAL = 30000; // 30 seconds

// Connect to the WebSocket server
export function connect() {
  // Close existing connection if any
  if (socket) {
    socket.close();
  }

  // Determine WebSocket URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  try {
    socket = new WebSocket(wsUrl);
    
    // Connection opened
    socket.addEventListener('open', (event) => {
      reconnectAttempts = 0;
      isIntentionalDisconnect = false;
      
      gameState.update(state => {
        // If we're reconnecting and have a player ID, send a reconnect message
        if (state.isReconnecting && state.playerId) {
          setTimeout(() => {
            sendMessage({
              type: 'reconnect',
              playerId: state.playerId,
              playerName: state.playerName
            });
          }, 500); // Small delay to ensure connection is fully established
        }
        
        return {
          ...state,
          isConnected: true,
          isReconnecting: false,
          connectionError: null
        };
      });
      
      console.log('Connected to WebSocket server');
      startPingInterval();
    });
    
    // Listen for messages
    socket.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Message from server:', data);
        
        // Handle different message types
        switch (data.type) {
          case 'joined':
            gameState.update(state => ({
              ...state,
              playerId: data.playerId
            }));
            break;
          
          case 'reconnected':
            gameState.update(state => ({
              ...state,
            }));
            // Clear the message after a short delay
            break;
          
          case 'lobby_state':
            console.log('Received updated lobby state:', data);
            gameState.update(state => ({
              ...state,
              players: data.players,
              allReady: data.allReady
            }));
            break;
          
          case 'game_started':
            gameState.update(state => ({
              ...state,
              gameStarted: true
            }));
            break;
          
          case 'game_over':
            gameState.update(state => ({
              ...state,
              gameOver: true
            }));
            break;
            
          case 'pong':
            // Got pong response from server
            console.log('Received pong from server');
            break;
          
          case 'error':
            gameState.update(state => ({
              ...state,
              connectionError: data.message
            }));
            console.error('Server error:', data.message);
            break;
        }
      } catch (err) {
        console.error('Error parsing message:', err);
      }
    });
    
    // Connection closed
    socket.addEventListener('close', (event) => {
      stopPingInterval();
      
      gameState.update(state => ({
        ...state,
        isConnected: false
      }));
      console.log('Disconnected from WebSocket server');
      
      // Start reconnection attempts if not deliberately disconnected
      if (!isIntentionalDisconnect) {
        attemptReconnect();
      }
    });
    
    // Connection error
    socket.addEventListener('error', (event) => {
      gameState.update(state => ({
        ...state,
        isConnected: false,
        connectionError: 'Failed to connect to WebSocket server'
      }));
      console.error('WebSocket error:', event);
    });
    
  } catch (err) {
    gameState.update(state => ({
      ...state,
      isConnected: false,
      connectionError: err.message
    }));
    console.error('WebSocket connection error:', err);
  }
}

// Attempt to reconnect
function attemptReconnect() {
  if (reconnectAttempts < maxReconnectAttempts) {
    reconnectAttempts++;
    
    gameState.update(state => ({
      ...state,
      isReconnecting: true,
      connectionError: getText('connection.reconnecting')
    }));
    
    console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
    
    // Clear any existing reconnect timer
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    
    // Try to reconnect after delay
    reconnectTimer = setTimeout(() => {
      connect();
    }, reconnectInterval);
  } else {
    gameState.update(state => ({
      ...state,
      isReconnecting: false,
      connectionError: getText('connection.reconnect_failed')
    }));
    console.log('Max reconnection attempts reached');
  }
}

// Start ping interval to keep connection alive
function startPingInterval() {
  stopPingInterval(); // Clear any existing interval
  
  pingInterval = setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      sendMessage({ type: 'ping' });
    }
  }, PING_INTERVAL);
}

// Stop ping interval
function stopPingInterval() {
  if (pingInterval) {
    clearInterval(pingInterval);
    pingInterval = null;
  }
}

// Send a message to the server
function sendMessage(message) {
  let connected = false;
  gameState.subscribe(state => {
    connected = state.isConnected;
  })();
  
  if (socket && connected) {
    const messageString = JSON.stringify(message);
    console.log('Sending message:', messageString);
    socket.send(messageString);
    return true;
  }
  return false;
}

// Join the lobby with a player name
export function joinLobby(playerName) {
  if (!playerName || !playerName.trim()) {
    return false;
  }
  
  gameState.update(state => ({
    ...state,
    playerName: playerName.trim()
  }));
  
  return sendMessage({
    type: 'join',
    name: playerName.trim()
  });
}

// Set player status to ready
export function setReady() {
  console.log('Setting player status to READY');
  return sendMessage({
    type: 'ready'
  });
}

// Set player status to unready
export function setUnready() {
  console.log('Setting player status to WAITING');
  return sendMessage({
    type: 'unready'
  });
}

// Start the game
export function startGame() {
  return sendMessage({
    type: 'start_game'
  });
}

// Mark player as dead
export function markAsDead() {
  return sendMessage({
    type: 'mark_dead'
  });
}

// Close the connection
export function disconnect() {
  isIntentionalDisconnect = true;
  
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  
  stopPingInterval();
  
  if (socket) {
    socket.close();
    socket = null;
  }
}

// Reset game state
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
    gameOver: false
  });
}

// Helper to get a player by ID
export function getPlayerById(players, playerId) {
  return players.find(p => p.id === playerId) || null;
}
