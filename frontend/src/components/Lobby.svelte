<script>
  import { onMount, onDestroy } from 'svelte';
  import { gameState, connect, disconnect, setReady, setUnready, startGame, markAsDead } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import PlayersList from './PlayersList.svelte';
  import JoinForm from './JoinForm.svelte';
  
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

<div class="lobby-container">
  <h2>{getText('lobby.title')}</h2>
  
  {#if !currentState.isConnected}
    <div class="connection-status error">
      {currentState.isReconnecting ? 
        getText('connection.reconnecting') : 
        getText('connection.connecting')}
    </div>
  {:else if currentState.connectionError}
    <div class="connection-status error">
      {currentState.connectionError}
    </div>
  {:else if !currentState.playerId}
    <JoinForm />
  {:else}
    <div class="connection-status success">
      {getText('connection.success', { playerName: currentState.playerName })}
    </div>
    
    <PlayersList />
    
    {#if currentState.gameStarted}
      <div class="game-container">
        <h3>{getText('game.title')}</h3>
        
        {#if currentState.gameOver}
          <div class="game-over">
            <h4>{getText('game.gameover_title')}</h4>
            <p>{getText('game.gameover_message')}</p>
          </div>
        {:else if currentPlayer?.status === 'ALIVE'}
          <div class="player-actions">
            <button class="death-button" onclick={markAsDead}>
              {getText('buttons.dead')}
            </button>
          </div>
        {:else}
          <div class="player-status-message">
            {getText('game.player_dead')}
          </div>
        {/if}
      </div>
    {:else}
      <!-- Only show controls if player exists -->
      {#if currentPlayer}
        <div class="lobby-controls">
          <button 
            onclick={handleReadyClick}
            class={currentPlayer.status === 'READY' ? 'cancel-button' : 'ready-button'}
          >
            {currentPlayer.status === 'READY' ? getText('buttons.cancel') : getText('buttons.ready')}
          </button>
          
          {#if currentState.allReady}
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
  {/if}
</div>

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
  
  .game-container {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    margin-top: 20px;
  }
  
  .death-button {
    background-color: #f44336;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    margin-top: 16px;
  }
  
  .death-button:hover {
    background-color: #d32f2f;
  }
  
  .game-over {
    background-color: #ffebee;
    padding: 16px;
    border-radius: 8px;
    margin-top: 16px;
  }
  
  .game-over h4 {
    color: #c62828;
    margin-top: 0;
  }
  
  .player-status-message {
    font-size: 18px;
    font-weight: bold;
    color: #f44336;
    margin-top: 16px;
  }
</style>
