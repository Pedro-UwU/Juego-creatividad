<script>
  import Lobby from './components/Lobby.svelte';
  import { getText } from './lib/textStore.js';
</script>

<main>
  <h1>{getText('app.title')}</h1>
  <p class="subtitle">{getText('app.subtitle')}</p>
  
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
