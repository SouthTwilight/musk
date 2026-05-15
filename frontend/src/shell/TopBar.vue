<template>
  <header class="topbar">
    <div class="topbar-left">
      <button
        v-if="appStore.sidebarCollapsed"
        class="menu-btn"
        @click="appStore.toggleSidebar()"
      >
        ☰
      </button>
      <span class="page-title">{{ pageTitle }}</span>
    </div>
    <div class="topbar-right">
      <button class="theme-btn" @click="toggleTheme" :title="themeTooltip">
        {{ appStore.theme === "dark" ? "☀️" : "🌙" }}
      </button>
      <div class="user-info">
        <span class="user-name">{{
          authStore.user?.username || "用户"
        }}</span>
        <button class="logout-btn" @click="handleLogout">退出</button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAppStore } from "@/stores/app";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const appStore = useAppStore();
const authStore = useAuthStore();

const pageTitle = computed(() => {
  if (route.path === "/") return "首页";
  if (route.path === "/settings") return "设置";
  return "Musk";
});

const themeTooltip = computed(() =>
  appStore.theme === "dark" ? "切换到浅色模式" : "切换到深色模式"
);

function toggleTheme() {
  appStore.setTheme(appStore.theme === "dark" ? "light" : "dark");
}

function handleLogout() {
  authStore.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.topbar {
  height: 52px;
  background-color: var(--bg-secondary, #161b22);
  border-bottom: 1px solid var(--border-primary, #30363d);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.menu-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary, #8b949e);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm, 6px);
}

.menu-btn:hover {
  background-color: var(--bg-tertiary, #21262d);
  color: var(--text-primary, #e6edf3);
}

.page-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.theme-btn {
  background: transparent;
  border: 1px solid var(--border-primary, #30363d);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 16px;
  padding: 4px 10px;
  transition: all 0.15s ease;
}

.theme-btn:hover {
  background-color: var(--bg-tertiary, #21262d);
  color: var(--accent, #58a6ff);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 13px;
  color: var(--text-secondary, #8b949e);
}

.logout-btn {
  background: transparent;
  border: 1px solid var(--border-primary, #30363d);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 12px;
  transition: all 0.15s ease;
}

.logout-btn:hover {
  border-color: var(--error, #f85149);
  color: var(--error, #f85149);
}
</style>
