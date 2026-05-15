<template>
  <aside :class="['sidebar', { collapsed: appStore.sidebarCollapsed }]">
    <div class="sidebar-header">
      <span v-if="!appStore.sidebarCollapsed" class="logo-text">Musk</span>
      <span v-else class="logo-letter">M</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        :class="['nav-item', { active: isActive(item.path) }]"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!appStore.sidebarCollapsed" class="nav-label">{{
          item.label
        }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <button class="collapse-btn" @click="appStore.toggleSidebar()">
        {{ appStore.sidebarCollapsed ? "▶" : "◀" }}
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
import { useAppStore } from "@/stores/app";

const route = useRoute();
const appStore = useAppStore();

const menuItems = [
  { path: "/", icon: "🏠", label: "首页" },
  { path: "/settings", icon: "⚙️", label: "设置" },
];

function isActive(path: string): boolean {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background-color: #010409;
  border-right: 1px solid var(--border-primary, #21262d);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid var(--border-secondary, #21262d);
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent, #58a6ff);
  white-space: nowrap;
}

.logo-letter {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent, #58a6ff);
}

.sidebar-nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm, 6px);
  color: var(--text-secondary, #8b949e);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.nav-item:hover {
  background-color: var(--bg-tertiary, #21262d);
  color: var(--text-primary, #e6edf3);
}

.nav-item.active {
  background-color: rgba(88, 166, 255, 0.15);
  color: var(--accent, #58a6ff);
  border-left: 2px solid var(--accent, #58a6ff);
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  padding: 8px;
  border-top: 1px solid var(--border-secondary, #21262d);
}

.collapse-btn {
  width: 100%;
  padding: 8px;
  background: transparent;
  border: 1px solid var(--border-primary, #30363d);
  border-radius: var(--radius-sm, 6px);
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s ease;
}

.collapse-btn:hover {
  background-color: var(--bg-tertiary, #21262d);
  color: var(--text-primary, #e6edf3);
}
</style>
