<script>
  import ChatBox from './components/ChatBox.svelte';
</script>

<main>
  <h1>WebSocket Test App</h1>
  <p>Send messages to test the WebSocket connection</p>
  
  <ChatBox />
</main>

<style>
  main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    text-align: center;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  }
  
  h1 {
    color: #ff3e00;
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }
</style>
