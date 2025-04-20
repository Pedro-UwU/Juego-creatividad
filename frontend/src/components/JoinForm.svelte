<script>
  import { gameState } from '../lib/gameStore.js';
  import { joinLobby } from '../lib/websocketService.js';
  import { getText } from '../lib/textStore.js';
  
  let playerName = '';
  let currentState;
  
  gameState.subscribe(state => {
    currentState = state;
  });
  
  function handleSubmit() {
    if (playerName.trim()) {
      joinLobby(playerName);
    }
  }
  
  function handleKeyDown(event) {
    if (event.key === 'Enter') {
      handleSubmit();
    }
  }
</script>

<div class="join-form">
  <h2>{getText('join.title')}</h2>
  
  {#if currentState.connectionError}
    <div class="error-message">
      {getText('connection.error', { message: currentState.connectionError })}
    </div>
  {/if}
  
  <div class="form-group">
    <label for="player-name">{getText('join.label')}</label>
    <input 
      id="player-name"
      type="text" 
      placeholder={getText('join.placeholder')}
      bind:value={playerName}
      onkeydown={handleKeyDown}
      disabled={!currentState.isConnected}
    />
  </div>
  
  <button 
    onclick={handleSubmit}
    disabled={!currentState.isConnected || !playerName.trim()}
    class="join-button"
  >
    {getText('join.button')}
  </button>
</div>

<style>
  .join-form {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 20px;
    max-width: 400px;
    margin: 0 auto;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  h2 {
    color: #333;
    margin-top: 0;
    margin-bottom: 20px;
    text-align: center;
  }
  
  .error-message {
    background-color: #ffebee;
    color: #f44336;
    padding: 8px;
    border-radius: 4px;
    margin-bottom: 16px;
    font-size: 14px;
  }
  
  .form-group {
    margin-bottom: 16px;
  }
  
  label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
  }
  
  input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 16px;
    box-sizing: border-box;
  }
  
  input:focus {
    border-color: #ff3e00;
    outline: none;
  }
  
  .join-button {
    background-color: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 16px;
    font-size: 16px;
    cursor: pointer;
    width: 100%;
    transition: background-color 0.2s;
  }
  
  .join-button:hover:not(:disabled) {
    background-color: #e03600;
  }
  
  .join-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
</style>
