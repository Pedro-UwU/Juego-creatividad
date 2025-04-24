<script>
  // Destructure props with defaults
  let {
    message,
    duration = 3000,
    type = 'info'
  } = $props();

  let visible = $state(true);

  $effect(() => {
    const timer = setTimeout(() => {
      visible = false;
    }, duration);

    return () => clearTimeout(timer);
  });
</script>

{#if visible}
  <div class="notification {type}">
    {message}
  </div>
{/if}

<style>
  .notification {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 10px 20px;
    border-radius: 4px;
    font-size: 16px;
    color: white;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    pointer-events: none;
    max-width: 90%;
    animation: slide-in 0.3s ease-out forwards;
  }

  @keyframes slide-in {
    0% { transform: translateX(-50%) translateY(-20px); opacity: 0; }
    100% { transform: translateX(-50%) translateY(0); opacity: 1; }
  }

  .info {
    background-color: rgba(33, 150, 243, 0.9);
  }

  .death {
    background-color: rgba(244, 67, 54, 0.9);
  }

  .sick {
    background-color: rgba(107, 142, 35, 0.9);
  }

  .cure {
    background-color: rgba(76, 175, 80, 0.9);
  }

  .round {
    background-color: rgba(156, 39, 176, 0.9);
  }

  .gameOver {
    background-color: rgba(255, 152, 0, 0.9);
    font-weight: bold;
    font-size: 18px;
    padding: 15px 25px;
  }
</style>

