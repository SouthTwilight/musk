<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="login-title">Musk</h1>
      <p class="login-subtitle">Sign in to continue</p>

      <!-- Tab Switcher -->
      <div class="tab-switcher">
        <button
          :class="['tab-btn', { active: mode === 'login' }]"
          @click="mode = 'login'"
        >
          Login
        </button>
        <button
          :class="['tab-btn', { active: mode === 'register' }]"
          @click="mode = 'register'"
        >
          Register
        </button>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Enter your username"
            required
            autocomplete="username"
          />
        </div>

        <div v-if="mode === 'register'" class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="Enter your email"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter your password"
            required
            autocomplete="current-password"
          />
        </div>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ mode === "login" ? "Sign In" : "Create Account" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const mode = ref<"login" | "register">("login");
const username = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function handleSubmit() {
  error.value = "";
  loading.value = true;

  try {
    if (mode.value === "register") {
      await authStore.register(username.value, email.value, password.value);
    } else {
      await authStore.login(username.value, password.value);
    }
    router.push("/");
  } catch (err: unknown) {
    if (err && typeof err === "object" && "response" in err) {
      const axiosErr = err as { response?: { data?: { detail?: string; message?: string } } };
      const data = axiosErr.response?.data;
      if (typeof data === "object" && data !== null) {
        error.value = data.detail || data.message || Object.values(data).flat().join(" ");
      } else {
        error.value = "An error occurred. Please try again.";
      }
    } else {
      error.value = "Network error. Please check your connection.";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 1rem;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--card-shadow);
  padding: 2.5rem;
}

.login-title {
  text-align: center;
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 0.25rem;
  letter-spacing: 2px;
}

.login-subtitle {
  text-align: center;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
}

/* Tab Switcher */
.tab-switcher {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  background: var(--bg-primary);
  border-radius: var(--radius-md);
  padding: 4px;
}

.tab-btn {
  flex: 1;
  padding: 0.6rem 1rem;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.tab-btn.active {
  background: var(--accent);
  color: var(--btn-primary-text);
}

.tab-btn:hover:not(.active) {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

/* Error Message */
.error-message {
  background: rgba(248, 81, 73, 0.1);
  border: 1px solid var(--error);
  color: var(--error);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  font-size: 0.85rem;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group input {
  padding: 0.7rem 0.9rem;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 0.9rem;
  transition: border-color var(--transition-fast);
  outline: none;
}

.form-group input::placeholder {
  color: var(--text-muted);
}

.form-group input:focus {
  border-color: var(--input-focus-border);
  box-shadow: 0 0 0 3px var(--accent-muted);
}

/* Submit Button */
.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--btn-primary-bg);
  color: var(--btn-primary-text);
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.submit-btn:hover:not(:disabled) {
  background: var(--btn-primary-hover);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
