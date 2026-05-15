<template>
  <div class="home-view">
    <h1>欢迎回来，{{ authStore.user?.username || "用户" }}</h1>
    <p class="subtitle">Musk 看板工具平台 — 框架核心 MVP 开发中</p>
    <div class="status-cards">
      <div class="status-card">
        <div class="status-icon">✅</div>
        <div class="status-info">
          <h3>Sprint 1</h3>
          <p>项目脚手架 + 认证系统</p>
        </div>
      </div>
      <div class="status-card active">
        <div class="status-icon">🔨</div>
        <div class="status-info">
          <h3>Sprint 2</h3>
          <p>框架壳 + 主题系统</p>
        </div>
      </div>
      <div class="status-card">
        <div class="status-icon">📋</div>
        <div class="status-info">
          <h3>Sprint 3</h3>
          <p>模块应用层 + AI 中枢</p>
        </div>
      </div>
      <div class="status-card">
        <div class="status-icon">🐳</div>
        <div class="status-info">
          <h3>Sprint 4</h3>
          <p>Docker 部署 + 集成验证</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();

onMounted(() => {
  if (!authStore.user) {
    authStore.fetchUser();
  }
});
</script>

<style scoped>
.home-view {
  max-width: 900px;
  margin: 0 auto;
}

.home-view h1 {
  font-size: 24px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 32px;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.status-card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md);
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  transition: all 0.2s ease;
}

.status-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}

.status-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.status-info h3 {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.status-info p {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
