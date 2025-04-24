import { getText } from './textStore.js';
import { 
  gameState,
  updateConnectionState, 
  updatePlayerInfo, 
  updateGameState, 
  updateRoleInfo,
  updateRoundInfo,
  resetGameState
} from './gameStore.js';
import { handleGameMessage } from './gameLogic.js';
import { get } from 'svelte/store';

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
        handleGameOver(data);
        break;
        
      // New round-based message handlers
      case 'round_started':
        handleRoundStarted(data);
        break;
        
      case 'sick_players':
        handleSickPlayers(data);
        break;
        
      case 'player_cured':
        handlePlayerCured(data);
        break;
        
      case 'no_player_cured':
        handleNoPlayerCured();
        break;
        
      case 'round_ended':
        handleRoundEnded(data);
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
      
      // If the player is now sick but wasn't before, trigger notification
      if (oldPlayer && 
          oldPlayer.status !== 'SICK' && 
          newPlayer.status === 'SICK') {
        import('./notificationStore.js').then(module => {
          module.notifyPlayerSick(newPlayer.name);
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
function handleGameOver(data) {
  updateGameState({ 
    gameOver: true,
    winner: data.winner || null  // Store the winning team
  });
  
  // Show winner notification
  if (data.winner) {
    import('./notificationStore.js').then(module => {
      module.notifyGameOver(data.winner);
    });
  }
}

// Handle error message
function handleError(data) {
  updateConnectionState({ connectionError: data.message });
  console.error('Server error:', data.message);
}

// New round-based message handlers
function handleRoundStarted(data) {
  console.log('Round started:', data.roundNumber);
  updateRoundInfo({
    currentRound: data.roundNumber,
    roundInProgress: true,
    sickPlayers: [], // Will be populated in handleSickPlayers
    playerCured: undefined
  });
  
  // Display round started notification
  import('./notificationStore.js').then(module => {
    module.notifyRoundStarted(data.roundNumber);
  });
}

function handleSickPlayers(data) {
  console.log('Sick players:', data.players);
  updateRoundInfo({
    sickPlayers: data.players
  });
}

function handlePlayerCured(data) {
  console.log('Player cured:', data.playerName, gameState);
  let state = get(gameState)
  updateRoundInfo({
    playerCured: true,
    sickPlayers: [...state.sickPlayers].filter(p => p.id !== data.playerId)
  });
  
  // Display player cured notification
  import('./notificationStore.js').then(module => {
    module.notifyPlayerCured(data.playerName);
  });
}

function handleNoPlayerCured() {
  console.log('No player cured this round');
  updateRoundInfo({
    playerCured: false
  });
}

function handleRoundEnded(data) {
  console.log('Round ended:', data.roundNumber);
  updateRoundInfo({
    roundInProgress: false,
    sickPlayers: []
  });
  
  // Display round ended notification
  import('./notificationStore.js').then(module => {
    module.notifyRoundEnded(data.roundNumber);
  });
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
