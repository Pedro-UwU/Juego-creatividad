  <script>
  import { connect, disconnect, sendMessage, getState } from '../lib/websockets.svelte.js';
  
  let inputMessage = $state('');
  const wsState = getState();
  
  // Connect when component mounts
  $effect(() => {
    connect();
    
    // Disconnect when component is destroyed
    return () => {
      disconnect();
    };
  });
  
  function handleSend() {
    if (inputMessage.trim() && wsState.isConnected) {
      sendMessage(inputMessage);
      inputMessage = '';
    }
  }
  
  function handleKeyDown(event) {
    if (event.key === 'Enter') {
      handleSend();
    }
  }
</script>

<div class="chat-container">
  <div class="status-bar">
    <div class="connection-status" class:connected={wsState.isConnected}>
      {wsState.isConnected ? 'Connected' : 'Disconnected'}
    </div>
    {#if wsState.connectionError}
      <div class="error-message">Error: {wsState.connectionError}</div>
    {/if}
    <button class="connect-button" onclick={wsState.isConnected ? disconnect : connect}>
      {wsState.isConnected ? 'Disconnect' : 'Connect'}
    </button>
  </div>
  
  <div class="messages-container">
    {#if wsState.messages.length === 0}
      <div class="no-messages">No messages yet</div>
    {:else}
      {#each wsState.messages as message}
        <div class="message" class:sent={!message.received} class:received={message.received}>
          {message.text}
        </div>
      {/each}
    {/if}
  </div>
  
  <div class="input-container">
    <input 
      type="text" 
      placeholder="Type a message..." 
      bind:value={inputMessage}
      onkeydown={handleKeyDown}
      disabled={!wsState.isConnected}
    />
    <button 
      class="send-button" 
      onclick={handleSend}
      disabled={!wsState.isConnected || !inputMessage.trim()}
    >
      Send
    </button>
  </div>
</div>

<style>
  .chat-container {
    display: flex;
    flex-direction: column;
    border: 1px solid #ccc;
    border-radius: 4px;
    height: 400px;
    width: 100%;
    max-width: 500px;
    margin: 0 auto;
  }
  
  .status-bar {
    display: flex;
    align-items: center;
    padding: 8px;
    background-color: #f5f5f5;
    border-bottom: 1px solid #ccc;
  }
  
  .connection-status {
    font-size: 14px;
    color: #ff3e00;
    margin-right: auto;
  }
  
  .connection-status.connected {
    color: #28a745;
  }
  
  .error-message {
    color: #dc3545;
    font-size: 12px;
    margin-right: 8px;
  }
  
  .connect-button {
    background-color: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    cursor: pointer;
  }
  
  .messages-container {
    flex-grow: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .no-messages {
    text-align: center;
    color: #6c757d;
    margin-top: 40px;
  }
  
  .message {
    padding: 8px 12px;
    border-radius: 16px;
    max-width: 80%;
    word-break: break-word;
  }
  
  .sent {
    background-color: #ff3e00;
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
  }
  
  .received {
    background-color: #f1f1f1;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
  }
  
  .input-container {
    display: flex;
    padding: 8px;
    border-top: 1px solid #ccc;
  }
  
  input {
    flex-grow: 1;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    margin-right: 8px;
  }
  
  .send-button {
    background-color: #ff3e00;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0 12px;
    cursor: pointer;
  }
  
  .send-button:disabled, .connect-button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
</style>
