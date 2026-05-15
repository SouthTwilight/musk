<template>
  <div class="settings-view">
    <h1>设置</h1>

    <section class="setting-section">
      <h2>外观</h2>
      <div class="setting-row">
        <div class="setting-label">
          <span class="setting-name">主题模式</span>
          <span class="setting-desc">切换深色/浅色主题</span>
        </div>
        <div class="setting-control">
          <button
            :class="['theme-option', { active: appStore.theme === 'dark' }]"
            @click="appStore.setTheme('dark')"
          >
            🌙 深色
          </button>
          <button
            :class="['theme-option', { active: appStore.theme === 'light' }]"
            @click="appStore.setTheme('light')"
          >
            ☀️ 浅色
          </button>
        </div>
      </div>
    </section>

    <section class="setting-section">
      <h2>背景图</h2>
      <div class="setting-row">
        <div class="setting-label">
          <span class="setting-name">自定义背景</span>
          <span class="setting-desc">上传图片作为内容区背景</span>
        </div>
        <div class="setting-control">
          <label class="upload-btn">
            选择图片
            <input
              type="file"
              accept="image/*"
              hidden
              @change="handleUpload"
            />
          </label>
          <button
            v-if="appStore.backgroundImage"
            class="clear-btn"
            @click="clearBackground"
          >
            清除背景
          </button>
        </div>
      </div>
      <div v-if="appStore.backgroundImage" class="bg-preview">
        <img :src="appStore.backgroundImage" alt="背景预览" />
      </div>
      <p v-if="uploadError" class="error">{{ uploadError }}</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useAppStore } from "@/stores/app";
import api from "@/core/api";

const appStore = useAppStore();
const uploadError = ref("");

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  uploadError.value = "";

  if (file.size > 5 * 1024 * 1024) {
    uploadError.value = "文件大小不能超过 5MB";
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post("/storage/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    appStore.setBackgroundImage(data.url || data.file);
  } catch {
    uploadError.value = "上传失败，请重试";
  }
}

function clearBackground() {
  appStore.setBackgroundImage("");
}
</script>

<style scoped>
.settings-view {
  max-width: 700px;
  margin: 0 auto;
}

.settings-view h1 {
  font-size: 24px;
  color: var(--text-primary);
  margin-bottom: 24px;
}

.setting-section {
  margin-bottom: 32px;
}

.setting-section h2 {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-primary);
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.setting-name {
  display: block;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.setting-desc {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
}

.setting-control {
  display: flex;
  gap: 8px;
  align-items: center;
}

.theme-option {
  padding: 8px 16px;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s ease;
}

.theme-option.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-muted, rgba(88, 166, 255, 0.15));
}

.upload-btn {
  display: inline-block;
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s ease;
}

.upload-btn:hover {
  opacity: 0.9;
}

.clear-btn {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
}

.clear-btn:hover {
  border-color: var(--error);
  color: var(--error);
}

.bg-preview {
  margin-top: 12px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-primary);
  max-height: 200px;
}

.bg-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  max-height: 200px;
}

.error {
  color: var(--error);
  font-size: 13px;
  margin-top: 8px;
}
</style>
