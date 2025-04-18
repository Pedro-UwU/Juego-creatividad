<script>
  import Lobby from './components/Lobby.svelte';
</script>

<main>
  <h1>Game Lobby</h1>
  <p class="subtitle">Connect, get ready, and play!</p>
  
  <Lobby />
</main>

<style>
  main {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  }
  
  h1 {
    color: #ff3e00;
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 0.5rem;
  }
  
  .subtitle {
    text-align: center;
    color: #444;
    margin-top: 0;
    margin-bottom: 2rem;
  }
</style>
