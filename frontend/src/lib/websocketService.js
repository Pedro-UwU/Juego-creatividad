import { getText } from './textStore.js';
import { 
  gameState,
  updateConnectionState, 
  updatePlayerInfo, 
  updateGameState, 
  updateRoleInfo,
  resetGameState
} from './gameStore.js';
import { handleGameMessage } from './gameLogic.js';

// Socket instance
let socket = null;

// Game tracking
let currentGameId = null;

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
      
      updateConnectionState({ 
        isConnected: true, 
        isReconnecting: false, 
        connectionError: null 
      });
      
      // Check if we need to send a reconnect message
      if (window.localStorage.getItem('playerId') && 
          window.localStorage.getItem('playerName') &&
          window.localStorage.getItem('gameId')) {
        setTimeout(() => {
          sendMessage({
            type: 'reconnect',
            playerId: window.localStorage.getItem('playerId'),
            playerName: window.localStorage.getItem('playerName'),
            gameId: window.localStorage.getItem('gameId')
          });
        }, 500);
      }
      
      console.log('Connected to WebSocket server');
      startPingInterval();
    });
    
    // Listen for messages
    socket.addEventListener('message', handleSocketMessage);
    
    // Connection closed
    socket.addEventListener('close', (event) => {
      stopPingInterval();
      
      updateConnectionState({ isConnected: false });
      console.log('Disconnected from WebSocket server');
      
      // Start reconnection attempts if not deliberately disconnected
      if (!isIntentionalDisconnect) {
        attemptReconnect();
      }
    });
    
    // Connection error
    socket.addEventListener('error', (event) => {
      updateConnectionState({
        isConnected: false,
        connectionError: 'Failed to connect to WebSocket server'
      });
      console.error('WebSocket error:', event);
    });
    
  } catch (err) {
    updateConnectionState({
      isConnected: false,
      connectionError: err.message
    });
    console.error('WebSocket connection error:', err);
  }
}

// Handle incoming WebSocket messages
function handleSocketMessage(event) {
  try {
    const data = JSON.parse(event.data);
    console.log('Message from server:', data);
    
    // Check for game_id_mismatch message type
    if (data.type === 'game_id_mismatch') {
      console.log('Game ID mismatch. Server has a different game. Forcing refresh...');
      clearSession();
      // Force a page reload
      window.location.reload();
      return;
    }
    
    // Check if game ID has changed (server restarted)
    if (data.type === 'lobby_state' && data.gameId) {
      const storedGameId = window.localStorage.getItem('gameId');
      
      // Only treat as a server restart if we already have a game ID stored
      // AND the game wasn't previously in progress but now is
      // (this avoids refreshing when a new game starts normally)
      if (storedGameId && 
          storedGameId !== data.gameId && 
          currentGameId &&
          !data.gameInProgress) {  // Only refresh if not transitioning to game in progress
        // Game ID has changed - server was restarted
        console.log('Server restarted with new game ID. Forcing refresh...');
        clearSession();
        // Force a page reload
        window.location.reload();
        return;
      }
      
      currentGameId = data.gameId;
      window.localStorage.setItem('gameId', data.gameId);
    }
    
    switch (data.type) {
      case 'joined':
        handleJoined(data);
        break;
      
      case 'reconnected':
        // No need for a message
        break;
      
      case 'lobby_state':
        handleLobbyState(data);
        break;
      
      case 'player_role':
        handlePlayerRole(data);
        break;
      
      case 'game_started':
        handleGameStarted();
        break;
      
      case 'game_over':
        handleGameOver();
        break;
        
      case 'pong':
        // Got pong response from server
        console.log('Received pong from server');
        break;
      
      case 'error':
        handleError(data);
        break;
        
      default:
        // Let gameLogic handle any custom game messages
        handleGameMessage(data);
        break;
    }
  } catch (err) {
    console.error('Error parsing message:', err);
  }
}

// Handle joined message
function handleJoined(data) {
  updatePlayerInfo({ playerId: data.playerId });
  
  // Save player ID and name to localStorage for reconnection
  if (data.playerId) {
    window.localStorage.setItem('playerId', data.playerId);
  }
}

// Handle lobby state update
function handleLobbyState(data) {
  console.log('Received updated lobby state:', data);
  
  // Check for newly dead players
  let currentState;
  gameState.subscribe(state => {
    currentState = state;
  })();
  
  // Only check for deaths if we have previous data
  if (currentState.players.length > 0 && data.players.length > 0) {
    data.players.forEach(newPlayer => {
      // Find matching player in old state
      const oldPlayer = currentState.players.find(p => p.id === newPlayer.id);
      
      // If the player is now dead but wasn't before, trigger notification
      if (oldPlayer && 
          oldPlayer.status !== 'DEAD' && 
          newPlayer.status === 'DEAD') {
        // Import needs to be inside function to avoid circular dependencies
        import('./notificationStore.js').then(module => {
          module.notifyPlayerDeath(newPlayer.name);
        });
      }
    });
  }
  
  updateGameState({
    players: data.players,
    allReady: data.allReady,
    gameInProgress: data.gameInProgress
  });
}

// Handle player role information
function handlePlayerRole(data) {
  console.log('Received player role info:', data.player);
  updateRoleInfo({
    playerRole: data.player.role,
    roleInfo: {
      baseRole: data.player.baseRole,
      isHeartbroken: data.player.isHeartbroken,
      color: data.player.color
    }
  });
}

// Handle game started message
function handleGameStarted() {
  updateGameState({ gameStarted: true });
}

// Handle game over message
function handleGameOver() {
  updateGameState({ gameOver: true });
}

// Handle error message
function handleError(data) {
  updateConnectionState({ connectionError: data.message });
  console.error('Server error:', data.message);
}

// Send a message to the server
export function sendMessage(message) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    const messageString = JSON.stringify(message);
    console.log('Sending message:', messageString);
    socket.send(messageString);
    return true;
  }
  return false;
}

// Attempt to reconnect
function attemptReconnect() {
  if (reconnectAttempts < maxReconnectAttempts) {
    reconnectAttempts++;
    
    updateConnectionState({
      isReconnecting: true,
      connectionError: getText('connection.reconnecting')
    });
    
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
    updateConnectionState({
      isReconnecting: false,
      connectionError: getText('connection.reconnect_failed')
    });
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

// Join the lobby with a player name
export function joinLobby(playerName) {
  if (!playerName || !playerName.trim()) {
    return false;
  }
  
  updatePlayerInfo({ playerName: playerName.trim() });
  window.localStorage.setItem('playerName', playerName.trim());
  
  return sendMessage({
    type: 'join',
    name: playerName.trim()
  });
}

// Clear all local storage and reset state
export function clearSession() {
  window.localStorage.removeItem('playerId');
  window.localStorage.removeItem('playerName');
  window.localStorage.removeItem('gameId');
  resetGameState();
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
