<template>
  <div class="article-detail">
    <div class="detail-header">
      <button class="back-btn" @click="router.push('/blog')">← 返回</button>
      <div class="header-actions">
        <button class="action-btn" @click="handleExport" title="导出 MD">📥 导出</button>
        <button class="action-btn" @click="handleReprocess" title="重新处理">🔄 重新处理</button>
      </div>
    </div>

    <div v-if="!article" class="loading">加载中...</div>
    <div v-else class="detail-body">
      <div class="note-panel">
        <h1 class="article-title">{{ article.title }}</h1>
        <div class="article-meta">
          <span>Source: <a :href="article.url" target="_blank">{{ article.source_name }}</a></span>
          <span v-if="article.score" class="score-badge" :class="scoreClass">⭐ {{ article.score }}/10</span>
        </div>

        <div class="note-section">
          <h3 class="section-label summary-label">📋 Summary</h3>
          <div class="section-content">{{ article.summary || '暂无总结' }}</div>
        </div>

        <div class="note-section">
          <h3 class="section-label points-label">🔑 Key Points</h3>
          <div class="section-content">
            <template v-if="parsedKeyPoints.length">
              <ul class="points-list">
                <li v-for="(point, i) in parsedKeyPoints" :key="i">{{ point }}</li>
              </ul>
            </template>
            <template v-else>{{ article.key_points || '暂无要点' }}</template>
          </div>
        </div>

        <div v-if="article.deep_analysis" class="note-section">
          <h3 class="section-label analysis-label">🔬 Deep Analysis</h3>
          <div class="section-content">{{ article.deep_analysis }}</div>
        </div>
      </div>

      <div class="source-panel">
        <div v-if="article.status === 'unparsable'" class="unparsable-notice">
          <p>⚠️ 无法提取正文内容</p>
          <a :href="article.url" target="_blank" class="open-link">在新标签页打开原文 →</a>
        </div>
        <template v-else>
          <iframe v-if="iframeOk" :src="article.url" class="source-iframe" @error="iframeOk = false" />
          <div v-else class="cached-content">
            <div class="cached-notice">⚠️ iframe 加载失败，展示缓存内容</div>
            <pre class="cached-text">{{ article.raw_text }}</pre>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useBlogStore } from "@/stores/blog";

const route = useRoute();
const router = useRouter();
const blogStore = useBlogStore();
const article = computed(() => blogStore.currentArticle);
const iframeOk = ref(true);

const scoreClass = computed(() => {
  if (!article.value?.score) return "";
  if (article.value.score >= 7) return "score-high";
  if (article.value.score >= 4) return "score-mid";
  return "score-low";
});

const parsedKeyPoints = computed(() => {
  const kp = article.value?.key_points;
  if (!kp) return [];
  try {
    const parsed = JSON.parse(kp);
    return Array.isArray(parsed) ? parsed : [];
  } catch { return []; }
});

onMounted(() => {
  blogStore.fetchArticle(Number(route.params.id));
  iframeOk.value = true;
});

async function handleExport() {
  if (!article.value) return;
  try {
    const blob = await blogStore.exportArticle(article.value.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${article.value.title.slice(0, 50)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  } catch { /* ignore */ }
}

async function handleReprocess() {
  if (!article.value) return;
  await blogStore.reprocessArticle(article.value.id);
  blogStore.fetchArticle(article.value.id);
}
</script>

<style scoped>
.article-detail { display: flex; flex-direction: column; height: calc(100vh - 52px - 48px); margin: -24px; }
.detail-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; border-bottom: 1px solid var(--border-primary);
  background: var(--bg-secondary); flex-shrink: 0;
}
.back-btn { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 14px; }
.header-actions { display: flex; gap: 8px; }
.action-btn {
  padding: 6px 12px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 12px;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }
.detail-body { display: flex; flex: 1; overflow: hidden; }
.note-panel { width: 33.33%; border-right: 1px solid var(--border-primary); padding: 24px; overflow-y: auto; }
.article-title { font-size: 20px; color: var(--text-primary); margin-bottom: 12px; line-height: 1.4; }
.article-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; font-size: 13px; color: var(--text-secondary); }
.article-meta a { color: var(--accent); }
.score-badge { font-weight: 600; }
.score-high { color: #bc8cff; }
.score-mid { color: var(--accent); }
.score-low { color: var(--text-muted); }
.note-section { margin-bottom: 20px; }
.section-label { font-size: 13px; margin-bottom: 8px; }
.summary-label { color: var(--accent); }
.points-label { color: #f78166; }
.analysis-label { color: #bc8cff; }
.section-content { font-size: 14px; color: var(--text-primary); line-height: 1.7; }
.points-list { padding-left: 18px; }
.points-list li { margin-bottom: 6px; }
.source-panel { flex: 1; display: flex; flex-direction: column; background: var(--bg-primary); }
.source-iframe { width: 100%; height: 100%; border: none; flex: 1; }
.cached-content { padding: 20px; overflow-y: auto; flex: 1; }
.cached-notice { color: var(--warning); font-size: 13px; margin-bottom: 12px; }
.cached-text { white-space: pre-wrap; font-size: 14px; color: var(--text-primary); line-height: 1.7; font-family: inherit; }
.unparsable-notice { padding: 60px 20px; text-align: center; color: var(--text-secondary); }
.unparsable-notice p { margin-bottom: 12px; }
.open-link { color: var(--accent); font-size: 14px; }
.loading { padding: 60px; text-align: center; color: var(--text-secondary); }
</style>
