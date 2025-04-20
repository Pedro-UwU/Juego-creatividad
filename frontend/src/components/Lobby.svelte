<script>
  import { onMount, onDestroy } from 'svelte';
  import { connect, disconnect, joinLobby } from '../lib/websocketService.js';
  import { setReady, setUnready, startGame } from '../lib/gameLogic.js';
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import PlayersList from './PlayersList.svelte';
  import JoinForm from './JoinForm.svelte';
  import GameView from './GameView.svelte';
  
  // Subscribe to the game state
  let currentState;
  let currentPlayer;
  let unsubscribe = gameState.subscribe(state => {
    currentState = state;
    currentPlayer = state.players.find(p => p.id === state.playerId);
  });
  
  // Handle visibility change (when user switches tabs or locks/unlocks phone)
  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      console.log('Page became visible - checking connection');
      // If we have a player ID but are disconnected, try to reconnect
      if (currentState.playerId && !currentState.isConnected && !currentState.isReconnecting) {
        console.log('Reconnecting due to visibility change');
        connect();
      }
    }
  }
  
  // Connect when component mounts and set up visibility listener
  onMount(() => {
    connect();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Add beforeunload handler to disconnect nicely when possible
    window.addEventListener('beforeunload', () => {
      disconnect();
    });
  });
  
  // Cleanup when component is destroyed
  onDestroy(() => {
    unsubscribe();
    document.removeEventListener('visibilitychange', handleVisibilityChange);
    disconnect();
  });
  
  // Handle ready/unready toggle
  function handleReadyClick() {
    if (!currentPlayer) return;
    
    console.log("Current player status:", currentPlayer.status);
    
    if (currentPlayer.status === 'READY') {
      console.log("Sending unready");
      setUnready();
    } else {
      console.log("Sending ready");
      setReady();
    }
  }
</script>

{#if currentState?.gameStarted}
  <GameView />
{:else}
  <div class="lobby-container">
    <h2>{getText('lobby.title')}</h2>
    
    {#if !currentState?.isConnected}
      <div class="connection-status error">
        {currentState?.isReconnecting ? 
          getText('connection.reconnecting') : 
          getText('connection.connecting')}
      </div>
    {:else if currentState?.connectionError}
      <div class="connection-status error">
        {currentState.connectionError}
      </div>
    {:else if !currentState?.playerId}
      <JoinForm />
    {:else}
      <div class="connection-status success">
        {getText('connection.success', { playerName: currentState.playerName })}
      </div>
      
      <PlayersList />
      
      <!-- Only show controls if player exists -->
      {#if currentPlayer}
        <div class="lobby-controls">
          <button 
            onclick={handleReadyClick}
            class={currentPlayer.status === 'READY' ? 'cancel-button' : 'ready-button'}
          >
            {currentPlayer.status === 'READY' ? getText('buttons.cancel') : getText('buttons.ready')}
          </button>
          
          {#if currentState.allReady && currentState.players.length >= 2}
            <button 
              onclick={startGame}
              class="start-button"
            >
              {getText('buttons.start')}
            </button>
          {/if}
        </div>
      {/if}
    {/if}
  </div>
{/if}

<style>
  .lobby-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 20px;
  }
  
  h2 {
    color: #333;
    text-align: center;
    margin-bottom: 20px;
  }
  
  .connection-status {
    text-align: center;
    padding: 10px;
    border-radius: 4px;
    margin-bottom: 20px;
  }
  
  .success {
    background-color: #e8f5e9;
    color: #2e7d32;
  }
  
  .error {
    background-color: #ffebee;
    color: #c62828;
  }
  
  .lobby-controls {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 20px;
  }
  
  .ready-button, .cancel-button {
    padding: 12px;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
    transition: background-color 0.2s;
    color: white;
  }
  
  .ready-button {
    background-color: #4caf50;
  }
  
  .ready-button:hover {
    background-color: #388e3c;
  }
  
  .cancel-button {
    background-color: #f44336;
  }
  
  .cancel-button:hover {
    background-color: #d32f2f;
  }
  
  .start-button {
    background-color: #2196f3;
    color: white;
    padding: 12px;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .start-button:hover {
    background-color: #1976d2;
  }
</style>
