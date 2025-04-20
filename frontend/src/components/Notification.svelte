<script>
  export let message = '';
  export let duration = 3000; // Display time in milliseconds
  export let type = 'info'; // Can be 'info', 'death', etc.

  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';

  let visible = true;
  
  onMount(() => {
    // Auto-hide after duration
    const timer = setTimeout(() => {
      visible = false;
    }, duration);
    
    return () => clearTimeout(timer);
  });
</script>

{#if visible}
  <div 
    class="notification {type}"
    in:fly={{ y: 20, duration: 300 }}
    out:fade={{ duration: 200 }}
  >
    {message}
  </div>
{/if}

<style>
  .notification {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 16px;
    color: white;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    pointer-events: none; /* Don't block clicks */
    max-width: 90%;
  }
  
  .info {
    background-color: rgba(33, 150, 243, 0.9);
  }
  
  .death {
    background-color: rgba(244, 67, 54, 0.9);
  }
</style>
