<script>
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import { derived } from 'svelte/store';

  // Subscribing automatically via $ syntax
  $: currentRound = $gameState.currentRound || 0;
  $: roundInProgress = $gameState.roundInProgress;
  $: gameStarted = $gameState.gameStarted;
  $: gameOver = $gameState.gameOver;

  // Derived value for round status text
  $: roundStatusText = (!gameStarted || gameOver)
    ? ''
    : currentRound === 0
      ? getText('rounds.waiting_for_first_round')
      : roundInProgress
        ? getText('rounds.in_progress')
        : getText('rounds.ended');
</script>

{#if gameStarted && !gameOver && currentRound > 0}
  <div class="round-indicator" class:active={roundInProgress}>
    <div class="round-number">{currentRound}</div>
    <div class="round-label">{getText('rounds.round_label')}</div>
    {#if roundStatusText}
      <div class="round-status">{roundStatusText}</div>
    {/if}
  </div>
{/if}

<style>
  .round-indicator {
    position: fixed;
    top: 20px;
    right: 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 10px;
    border-radius: 8px;
    z-index: 100;
    transition: all 0.3s ease;
  }

  .round-indicator.active {
    background-color: rgba(107, 142, 35, 0.8);
    box-shadow: 0 0 15px rgba(107, 142, 35, 0.5);
  }

  .round-number {
    font-size: 32px;
    font-weight: bold;
    line-height: 1;
  }

  .round-label {
    font-size: 14px;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .round-status {
    font-size: 12px;
    margin-top: 6px;
    padding: 2px 6px;
    background-color: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    white-space: nowrap;
  }
</style>

