<script>
  import { notifications } from '../lib/notificationStore.js';
  import Notification from './Notification.svelte';
</script>

<div class="notification-container">
  {#each $notifications as notification (notification.id)}
    <Notification 
      message={notification.message}
      type={notification.type}
      duration={notification.duration}
    />
  {/each}
</div>

<style>
  .notification-container {
    position: fixed;
    top: 20px;
    left: 0;
    right: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    z-index: 1000;
    pointer-events: none; /* Allow clicks to pass through */
  }
</style>
