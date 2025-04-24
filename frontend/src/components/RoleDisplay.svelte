<script>
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import { getRoleDisplayText, getRoleDescription } from '../lib/gameLogic.js';

  // Auto-subscribe to the gameState store
  $: state = $gameState;

  // Get the current player
  $: player = state.players?.find(p => p.id === state.playerId);

  // Check if current player is dead or sick
  $: isPlayerDead = player?.status === 'DEAD';
  $: isPlayerSick = player?.status === 'SICK';

  // Role text and description
  $: roleText = getRoleDisplayText(state.playerRole);
  $: roleDescription = getRoleDescription(state.playerRole);

  // Generate inline style for background color
  $: backgroundStyle = (() => {
    if (isPlayerDead) return 'background-color: #000000';
    if (isPlayerSick) return 'background-color: #6B8E23';
    return state.roleInfo?.color ? `background-color: ${state.roleInfo.color}` : '';
  })();
</script>

<div class="role-screen" style={backgroundStyle}>
  <div class="role-card" class:dead={isPlayerDead} class:sick={isPlayerSick}>
    <h1 class="role-title">{roleText}</h1>
    <p class="role-description">{roleDescription}</p>

    {#if state.roleInfo?.isHeartbroken}
      <div class="heartbroken-indicator">💔</div>
    {/if}

    <div class="status-indicator">
      {#if isPlayerDead}
        <p class="dead-status">{getText('player.you_are_dead')}</p>
      {:else if isPlayerSick}
        <p class="sick-status">{getText('player.you_are_sick')}</p>
      {:else if state.gameStarted && !state.gameOver}
        <p>{getText('player.game_in_progress')}</p>
      {:else if state.gameOver}
        <p>{getText('player.game_over')}</p>
      {/if}
    </div>

    {#if state.playerRole === 'DOCTOR'}
      <div class="doctor-note">
        <p>{getText('player.doctor_reminder')}</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .role-screen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    transition: background-color 1s ease;
  }

  .role-card {
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    padding: 2rem;
    max-width: 80%;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: background-color 0.5s ease;
  }

  .role-card.dead {
    background-color: rgba(50, 50, 50, 0.9);
    color: #fff;
  }

  .role-card.sick {
    background-color: rgba(107, 142, 35, 0.9);
    color: #fff;
  }

  .role-title {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #333;
  }

  .dead .role-title,
  .dead .role-description,
  .dead .status-indicator,
  .sick .role-title,
  .sick .role-description,
  .sick .status-indicator {
    color: #fff;
  }

  .role-description {
    font-size: 1.2rem;
    line-height: 1.5;
    margin-bottom: 1.5rem;
    color: #555;
  }

  .heartbroken-indicator {
    font-size: 3rem;
    margin: 1rem 0;
    animation: pulse 2s infinite;
  }

  .status-indicator {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #ddd;
    font-style: italic;
    color: #666;
  }

  .dead-status {
    color: #f44336;
    font-weight: bold;
    font-size: 1.5rem;
    animation: blink 1.5s infinite;
  }

  .sick-status {
    color: #ffeb3b;
    font-weight: bold;
    font-size: 1.5rem;
    animation: pulse 1.5s infinite;
  }

  .doctor-note {
    margin-top: 1rem;
    font-weight: bold;
    color: #2196F3;
    padding: 0.5rem;
    border: 1px dashed #2196F3;
    border-radius: 4px;
  }

  .dead .doctor-note {
    border-color: #90caf9;
    color: #90caf9;
  }

  .sick .doctor-note {
    border-color: #e3f2fd;
    color: #e3f2fd;
  }

  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }

  @keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }
</style>

