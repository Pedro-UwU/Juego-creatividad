<script>
  import { onDestroy } from 'svelte';
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import { startRound, curePlayer, endRound } from '../lib/gameLogic.js';

  let showCureOptions = false;
  let selectedPlayer = null;
  let currentState;

  // Subscribe to gameState and update currentState reactively
  const unsubscribe = gameState.subscribe((state) => {
    currentState = state;
  });

  onDestroy(unsubscribe);

  $: isDoctor = currentState?.playerRole === 'DOCTOR';
  $: roundInProgress = currentState?.roundInProgress;
  $: roundNumber = currentState?.currentRound || 0;
  $: sickPlayers = currentState?.sickPlayers || [];
  $: playerCured = currentState?.playerCured;
  $: gameOver = currentState?.gameOver;

  function handleStartRound() {
    startRound();
    showCureOptions = true;
    selectedPlayer = null;
  }

  function handleCurePlayer(playerId, playerName) {
    selectedPlayer = { id: playerId, name: playerName };
    curePlayer(playerId);
  }

  function handleNoCure() {
    selectedPlayer = null;
    curePlayer(null);
  }

  function handleEndRound() {
    endRound();
    showCureOptions = false;
    selectedPlayer = null;
  }
</script>

<div class="doctor-controls">
  {#if isDoctor}
    <div class="doctor-panel">
      <h2>{getText('doctor.title')}</h2>

      {#if !roundInProgress}
        <button
          class="start-round-button"
          on:click={handleStartRound}
          disabled={gameOver}
        >
          {getText('rounds.start_round')}
        </button>
      {:else}
        <div class="round-status">
          <h3>{getText('rounds.title', { roundNumber })}</h3>

          {#if showCureOptions && sickPlayers.length > 0}
            <div class="cure-options">
              <p>{getText('doctor.choose_player')}</p>
              <ul class="sick-players-list">
                {#each sickPlayers as player}
                  <li>
                    <button
                      on:click={() => handleCurePlayer(player.id, player.name)}
                      class:selected={selectedPlayer?.id === player.id}
                    >
                      {player.name}
                    </button>
                  </li>
                {/each}
                <li>
                  <button
                    on:click={handleNoCure}
                    class:selected={selectedPlayer === null && playerCured === false}
                  >
                    {getText('rounds.no_cure')}
                  </button>
                </li>
              </ul>
            </div>
          {:else if sickPlayers.length === 0}
            <p>{getText('doctor.no_sick_players')}</p>
          {/if}

          {#if playerCured !== undefined}
            <div class="cure-confirmation">
              {#if playerCured}
                <p>{getText('doctor.player_cured', { playerName: selectedPlayer?.name })}</p>
              {:else}
                <p>{getText('doctor.no_player_cured')}</p>
              {/if}
            </div>
          {/if}

          <button
            class="end-round-button"
            on:click={handleEndRound}
          >
            {getText('rounds.end_round')}
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .doctor-controls {
    margin-top: 20px;
  }
  
  .doctor-panel {
    background-color: #f0f8ff;
    border: 2px solid #4CAF50;
    border-radius: 8px;
    padding: 16px;
    max-width: 600px;
    margin: 0 auto;
  }
  
  h2 {
    color: #4CAF50;
    text-align: center;
    margin-top: 0;
  }
  
  h3 {
    color: #2196F3;
    text-align: center;
  }
  
  .round-status {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .cure-options {
    text-align: center;
    margin: 16px 0;
  }
  
  .sick-players-list {
    list-style: none;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
  }
  
  .sick-players-list button {
    width: 100%;
    padding: 8px 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: white;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .sick-players-list button:hover {
    background-color: #f0f0f0;
  }
  
  .sick-players-list button.selected {
    background-color: #e3f2fd;
    border-color: #2196F3;
    font-weight: bold;
  }
  
  .cure-confirmation {
    margin: 16px 0;
    padding: 12px;
    background-color: #e8f5e9;
    border-radius: 4px;
    text-align: center;
  }
  
  .start-round-button, .end-round-button {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.2s;
    margin-top: 16px;
  }
  
  .start-round-button:hover, .end-round-button:hover {
    background-color: #388E3C;
  }
  
  .start-round-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
  
  .end-round-button {
    background-color: #F44336;
  }
  
  .end-round-button:hover {
    background-color: #D32F2F;
  }
</style>

