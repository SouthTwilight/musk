<template>
  <div class="app-layout">
    <Sidebar />
    <div class="main-area">
      <TopBar />
      <main class="content-area" :style="bgStyle">
        <div class="content-overlay">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useAppStore } from "@/stores/app";
import Sidebar from "./Sidebar.vue";
import TopBar from "./TopBar.vue";

const appStore = useAppStore();

onMounted(() => {
  appStore.loadConfig();
});

const bgStyle = computed(() => {
  if (!appStore.backgroundImage) return {};
  return {
    backgroundImage: `url(${appStore.backgroundImage})`,
    backgroundSize: "cover",
    backgroundPosition: "center",
  };
});
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

.content-overlay {
  min-height: 100%;
  background: var(--bg-primary);
  opacity: 0.94;
  padding: 24px;
}

/* 如果有背景图，overlay 变为半透明遮罩 */
.content-area:has(.content-overlay) {
  background-color: var(--bg-primary);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
