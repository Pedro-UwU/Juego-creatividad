<script>
  import { gameState } from '../lib/gameStore.js';
  import { getText } from '../lib/textStore.js';
  
  // Subscribe to the game state
  let currentState;
  gameState.subscribe(state => {
    currentState = state;
  });
  
  // Function to get a status class
  function getStatusClass(status) {
    switch (status) {
      case 'WAITING': return 'status-waiting';
      case 'READY': return 'status-ready';
      case 'ALIVE': return 'status-alive';
      case 'DEAD': return 'status-dead';
      default: return '';
    }
  }
</script>

<div class="players-list">
  <h3>Players</h3>
  
  {#if !currentState || currentState.players.length === 0}
    <p class="empty-message">{getText('lobby.noplayers')}</p>
  {:else}
    <ul>
      {#each currentState.players as player}
        <li class:current={player.id === currentState.playerId}>
          <span class="player-name">{player.name}</span>
          <span class="player-status {getStatusClass(player.status)}">{player.status}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .players-list {
    background-color: #f5f5f5;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  h3 {
    margin-top: 0;
    color: #333;
    margin-bottom: 12px;
  }
  
  .empty-message {
    color: #666;
    font-style: italic;
    text-align: center;
  }
  
  ul {
    list-style-type: none;
    padding: 0;
    margin: 0;
  }
  
  li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    border-bottom: 1px solid #ddd;
  }
  
  li:last-child {
    border-bottom: none;
  }
  
  li.current {
    background-color: #fff3e0;
    border-radius: 4px;
    font-weight: bold;
  }
  
  .player-name {
    font-size: 16px;
  }
  
  .player-status {
    font-size: 14px;
    padding: 4px 8px;
    border-radius: 12px;
    color: white;
  }
  
  .status-waiting {
    background-color: #9e9e9e;
  }
  
  .status-ready {
    background-color: #4caf50;
  }
  
  .status-alive {
    background-color: #2196f3;
  }
  
  .status-dead {
    background-color: #f44336;
  }
</style>
