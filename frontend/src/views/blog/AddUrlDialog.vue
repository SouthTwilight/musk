<template>
  <div v-if="visible" class="dialog-overlay" @click.self="$emit('close')">
    <div class="dialog">
      <h3>添加文章链接</h3>
      <input v-model="url" class="dialog-input" placeholder="https://example.com/article" @keydown.enter="handleFetch" />
      <select v-model="categoryId" class="dialog-select">
        <option :value="undefined">自动分类</option>
        <option v-for="cat in blogStore.categories" :key="cat.id" :value="cat.id">
          {{ cat.icon }} {{ cat.name }}
        </option>
      </select>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="dialog-actions">
        <button class="btn-cancel" @click="$emit('close')">取消</button>
        <button class="btn-primary" @click="handleFetch" :disabled="!url.trim() || fetching">
          {{ fetching ? '抓取中...' : '抓取' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useBlogStore } from "@/stores/blog";

defineProps<{ visible: boolean }>();
const emit = defineEmits<{ close: []; fetched: [] }>();

const blogStore = useBlogStore();
const url = ref("");
const categoryId = ref<number | undefined>(undefined);
const fetching = ref(false);
const error = ref("");

async function handleFetch() {
  if (!url.value.trim()) return;
  fetching.value = true;
  error.value = "";
  try {
    await blogStore.fetchUrl(url.value.trim(), categoryId.value);
    url.value = "";
    emit("fetched");
    emit("close");
  } catch (e: any) {
    error.value = e.response?.data?.detail || "抓取失败";
  } finally {
    fetching.value = false;
  }
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: var(--bg-secondary); border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg); padding: 24px; width: 480px; max-width: 90vw;
}
.dialog h3 { margin-bottom: 16px; color: var(--text-primary); }
.dialog-input, .dialog-select {
  width: 100%; padding: 10px 12px; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm);
  color: var(--text-primary); font-size: 14px; margin-bottom: 12px;
}
.dialog-input:focus, .dialog-select:focus { border-color: var(--input-focus-border); outline: none; }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 8px 16px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer;
}
.btn-primary {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: var(--error); font-size: 13px; }
</style>
