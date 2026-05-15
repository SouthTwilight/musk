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
        <span v-if="!appStore.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>

      <div v-if="moduleItems.length > 0" class="nav-divider"></div>

      <router-link
        v-for="item in moduleItems"
        :key="item.path"
        :to="item.path"
        :class="['nav-item', { active: isActive(item.path) }]"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!appStore.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>

      <div class="nav-divider"></div>

      <router-link
        v-for="item in fixedItems"
        :key="item.path"
        :to="item.path"
        :class="['nav-item', { active: isActive(item.path) }]"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span v-if="!appStore.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
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
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useAppStore } from "@/stores/app";
import { fetchModules, type ModuleInfo } from "@/core/module";

const route = useRoute();
const appStore = useAppStore();

// 基础菜单（始终存在）
const menuItems = ref([
  { path: "/", icon: "🏠", label: "首页" },
]);

// 动态模块菜单
const moduleItems = ref<{ path: string; icon: string; label: string }[]>([]);

// 固定底部菜单
const fixedItems = [
  { path: "/ai", icon: "🤖", label: "AI 助手" },
  { path: "/settings", icon: "⚙️", label: "设置" },
];

onMounted(async () => {
  const modules = await fetchModules();
  moduleItems.value = modules.map((m) => ({
    path: m.url_prefix.replace(/^\/api\//, "/").replace(/\/$/, ""),
    icon: m.icon,
    label: m.display_name,
  }));
});

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

.nav-divider {
  height: 1px;
  background: var(--border-secondary, #21262d);
  margin: 8px 12px;
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
