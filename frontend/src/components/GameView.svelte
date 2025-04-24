<script>
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import { markAsDead } from '../lib/gameLogic.js';
  import RoleDisplay from './RoleDisplay.svelte';
  import DoctorControls from './DoctorControls.svelte';
  import RoundIndicator from './RoundIndicator.svelte';

  let currentState;
  $: gameState.subscribe(state => currentState = state);

  $: currentPlayer = currentState?.players?.find(p => p.id === currentState.playerId);
  $: isDoctor = currentPlayer?.role === 'DOCTOR';
  $: winner = currentState?.winner;
  $: showWinner = currentState?.gameOver && winner;
</script>

<div class="game-view">
  {#if currentState?.gameStarted}
    <RoleDisplay />
    <RoundIndicator />

    <div class="game-controls">
      {#if !currentState.gameOver}
        {#if currentPlayer?.status === 'ALIVE'}
          {#if isDoctor}
            <DoctorControls />
          {:else}
            <button 
              class="death-button" 
              on:click={markAsDead}
            >
              {getText('buttons.dead')}
            </button>
          {/if}
        {:else if currentPlayer?.status === 'DEAD'}
          <div class="death-status">
            {getText('player.you_are_dead')}
          </div>
        {:else if currentPlayer?.status === 'SICK'}
          <div class="sick-status">
            {getText('player.you_are_sick')}
          </div>
        {/if}
      {:else}
        <div class="game-over-message">
          <h2>{getText('game.gameover_title')}</h2>

          {#if showWinner}
            <p class="winner-message">{getText('game.winner', { team: winner })}</p>
            <p>{winner === 'ALLY' 
              ? getText('game.allies_win') 
              : getText('game.enemies_win')}</p>
          {:else}
            <p>{getText('game.gameover_message')}</p>
          {/if}
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

  .death-status,
  .sick-status {
    color: white;
    padding: 12px 24px;
    border-radius: 4px;
    font-size: 18px;
    font-weight: bold;
    margin-top: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .death-status {
    background-color: rgba(244, 67, 54, 0.9);
  }

  .sick-status {
    background-color: rgba(107, 142, 35, 0.9);
    animation: pulse 2s infinite;
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

  .winner-message {
    font-size: 1.5em;
    font-weight: bold;
    margin: 1em 0;
  }

  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
  }
</style>

