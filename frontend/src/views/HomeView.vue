<template>
  <div class="home-container">
    <header class="home-header">
      <h1 class="home-logo">Musk</h1>
      <button class="logout-btn" @click="handleLogout">Sign Out</button>
    </header>

    <main class="home-main">
      <div class="welcome-card">
        <h2 class="welcome-title">Welcome back</h2>
        <p v-if="authStore.user" class="welcome-username">
          {{ authStore.user.username }}
        </p>
        <p v-else class="welcome-username loading-text">Loading...</p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  await authStore.fetchUser();
});

function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.home-logo {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 1px;
}

.logout-btn {
  padding: 0.5rem 1.25rem;
  background: transparent;
  border: 1px solid var(--border-primary);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.logout-btn:hover {
  border-color: var(--error);
  color: var(--error);
  background: rgba(248, 81, 73, 0.08);
}

.home-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.welcome-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--card-shadow);
  padding: 3rem 4rem;
  text-align: center;
}

.welcome-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.75rem;
}

.welcome-username {
  font-size: 1.1rem;
  color: var(--accent);
  font-weight: 500;
}

.loading-text {
  color: var(--text-muted);
  font-style: italic;
}
</style>
