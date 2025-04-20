<script>
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import { markAsDead, endGame } from '../lib/gameLogic.js';
  import RoleDisplay from './RoleDisplay.svelte';
  
  // Subscribe to the game state
  let currentState;
  gameState.subscribe(state => {
    currentState = state;
  });
  
  // Computed property for current player
  $: currentPlayer = currentState?.players?.find(p => p.id === currentState?.playerId);
  
  // Check if player is the doctor
  $: isDoctor = currentPlayer?.role === 'DOCTOR';
</script>

<div class="game-view">
  {#if currentState?.gameStarted}
    <RoleDisplay />
    
    <div class="game-controls">
      {#if !currentState.gameOver}
        {#if currentPlayer?.status === 'ALIVE'}
          {#if isDoctor}
            <!-- Doctor controls -->
            <div class="doctor-controls">
              <p class="doctor-note">{getText('doctor.end_game_description')}</p>
              <button 
                class="end-game-button" 
                onclick={endGame}
              >
                {getText('buttons.end_game')}
              </button>
            </div>
          {:else}
            <!-- Non-doctor players can mark themselves as dead -->
            <button 
              class="death-button" 
              onclick={markAsDead}
            >
              {getText('buttons.dead')}
            </button>
          {/if}
        {:else if currentPlayer?.status === 'DEAD'}
          <div class="death-status">
            You are dead!
          </div>
        {/if}
      {:else}
        <div class="game-over-message">
          <h2>{getText('game.gameover_title')}</h2>
          <p>{getText('game.gameover_message')}</p>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .game-view {
    position: relative;
  }
  
  .game-controls {
    position: fixed;
    bottom: 20px;
    left: 0;
    right: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    z-index: 10;
  }
  
  .death-button {
    background-color: #f44336;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: background-color 0.2s;
  }
  
  .death-button:hover:not(:disabled) {
    background-color: #d32f2f;
  }
  
  .death-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  
  .death-status {
    background-color: rgba(244, 67, 54, 0.9);
    color: white;
    padding: 12px 24px;
    border-radius: 4px;
    font-size: 18px;
    font-weight: bold;
    margin-top: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
  
  .doctor-controls {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
  
  .doctor-note {
    color: #4CAF50;
    font-size: 16px;
    margin-bottom: 12px;
    text-align: center;
  }
  
  .end-game-button {
    background-color: #4CAF50;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    transition: background-color 0.2s;
  }
  
  .end-game-button:hover {
    background-color: #388E3C;
  }
  
  .game-over-message {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 16px 32px;
    border-radius: 8px;
    text-align: center;
    max-width: 80%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
  
  .game-over-message h2 {
    color: #f44336;
    margin-top: 0;
  }
</style>
