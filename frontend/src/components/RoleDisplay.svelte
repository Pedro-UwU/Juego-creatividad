<script>
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  import { getRoleDisplayText, getRoleDescription } from '../lib/gameLogic.js';
  
  // Subscribe to the game state
  let currentState;
  gameState.subscribe(state => {
    currentState = state;
  });
  
  // Generate inline style for background color based on player status and role
  $: backgroundStyle = (() => {
    // Check if player is dead
    if (currentState?.players?.find(p => p.id === currentState?.playerId)?.status === 'DEAD') {
      return 'background-color: #000000'; // Black background for dead players
    }
    // Otherwise use role color
    return currentState?.roleInfo?.color 
      ? `background-color: ${currentState.roleInfo.color}` 
      : '';
  })();
  
  // Get role text
  $: roleText = getRoleDisplayText(currentState?.playerRole);
  
  // Get role description
  $: roleDescription = getRoleDescription(currentState?.playerRole);
  
  // Check if current player is dead
  $: isPlayerDead = currentState?.players?.find(p => p.id === currentState?.playerId)?.status === 'DEAD';
</script>

<div class="role-screen" style={backgroundStyle}>
  <div class="role-card" class:dead={isPlayerDead}>
    <h1 class="role-title">{roleText}</h1>
    <p class="role-description">{roleDescription}</p>
    
    {#if currentState?.roleInfo?.isHeartbroken}
      <div class="heartbroken-indicator">💔</div>
    {/if}
    
    <div class="status-indicator">
      {#if isPlayerDead}
        <p class="dead-status">{getText('player.you_are_dead')}</p>
      {:else if currentState?.gameStarted && !currentState?.gameOver}
        <p>{getText('player.game_in_progress')}</p>
      {:else if currentState?.gameOver}
        <p>{getText('player.game_over')}</p>
      {/if}
    </div>
    
    {#if currentState?.playerRole === 'DOCTOR'}
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
  
  .role-title {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #333;
  }
  
  .dead .role-title,
  .dead .role-description,
  .dead .status-indicator {
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
