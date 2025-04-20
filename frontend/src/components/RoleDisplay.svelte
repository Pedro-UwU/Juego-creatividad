<script>
  import { gameState } from '../lib/gameStore.js';
  import { getRoleDisplayText, getRoleDescription } from '../lib/gameLogic.js';
  
  // Subscribe to the game state
  let currentState;
  gameState.subscribe(state => {
    currentState = state;
  });
  
  // Generate inline style for background color
  $: backgroundStyle = currentState?.roleInfo?.color 
    ? `background-color: ${currentState.roleInfo.color}` 
    : '';
  
  // Get role text
  $: roleText = getRoleDisplayText(currentState?.playerRole);
  
  // Get role description
  $: roleDescription = getRoleDescription(currentState?.playerRole);
</script>

<div class="role-screen" style={backgroundStyle}>
  <div class="role-card">
    <h1 class="role-title">{roleText}</h1>
    <p class="role-description">{roleDescription}</p>
    
    {#if currentState?.roleInfo?.isHeartbroken}
      <div class="heartbroken-indicator">💔</div>
    {/if}
    
    <div class="status-indicator">
      {#if currentState?.gameStarted && !currentState?.gameOver}
        <p>Game is in progress...</p>
      {:else if currentState?.gameOver}
        <p>Game over!</p>
      {/if}
    </div>
    
    {#if currentState?.playerRole === 'DOCTOR'}
      <div class="doctor-note">
        <p>Remember: You cannot die until all others are dead.</p>
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
  }
  
  .role-title {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #333;
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
  
  .doctor-note {
    margin-top: 1rem;
    font-weight: bold;
    color: #2196F3;
    padding: 0.5rem;
    border: 1px dashed #2196F3;
    border-radius: 4px;
  }
  
  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }
</style>
