<template>
  <div class="article-detail">
    <div class="detail-header">
      <button class="back-btn" @click="router.push('/blog')">← 返回</button>
      <div class="header-actions">
        <button v-if="editing" class="action-btn save-btn" @click="handleSave" title="保存">✓ 保存</button>
        <button v-if="editing" class="action-btn" @click="cancelEdit" title="取消">✗ 取消</button>
        <button v-if="!editing" class="action-btn" @click="startEdit" title="编辑">✏️ 编辑</button>
        <button class="action-btn" @click="handleExport" title="导出 MD">📥 导出</button>
        <button class="action-btn" @click="handleReprocess" title="重新处理">🔄 重新处理</button>
      </div>
    </div>

    <div v-if="!article" class="loading">加载中...</div>
    <div v-else class="detail-body">
      <div class="note-panel">
        <!-- Title -->
        <template v-if="editingField('title')">
          <input v-model="form.title" class="edit-input title-input" />
        </template>
        <template v-else>
          <h1 class="article-title editable" @click="focusField('title')">{{ form.title }}</h1>
        </template>

        <div class="article-meta">
          <span>Source: <a :href="article.url" target="_blank">{{ article.source_name }}</a></span>
          <span v-if="article.score" class="score-badge" :class="scoreClass">⭐ {{ article.score }}/10</span>
          <template v-if="editing">
            <select v-model="form.categoryId" class="category-select">
              <option :value="null">未分类</option>
              <option v-for="cat in blogStore.categories" :key="cat.id" :value="cat.id">{{ cat.icon }} {{ cat.name }}</option>
            </select>
          </template>
          <span v-else class="category-badge" @click="startEdit">{{ article.category_name ? `${article.category_icon} ${article.category_name}` : '未分类（点击编辑）' }}</span>
        </div>

        <!-- Summary -->
        <div class="note-section">
          <h3 class="section-label summary-label">📋 Summary</h3>
          <template v-if="editing">
            <textarea v-model="form.summary" class="edit-textarea" rows="5" />
          </template>
          <template v-else>
            <div v-if="article.summary" class="section-content md-render editable" @click="focusField('summary')" v-html="renderMd(article.summary)" />
            <div v-else class="section-content editable placeholder" @click="focusField('summary')">暂无总结（点击编辑）</div>
          </template>
        </div>

        <!-- Key Points -->
        <div class="note-section">
          <h3 class="section-label points-label">🔑 Key Points</h3>
          <template v-if="editing">
            <textarea v-model="form.keyPointsText" class="edit-textarea" rows="6" placeholder="每行一个要点" />
          </template>
          <template v-else>
            <div class="section-content">
              <div v-if="article.key_points" class="md-render editable" @click="focusField('key_points')" v-html="renderMd(article.key_points)" />
              <span v-else class="editable placeholder" @click="focusField('key_points')">暂无要点（点击编辑）</span>
            </div>
          </template>
        </div>

        <!-- Deep Analysis -->
        <div v-if="article.deep_analysis || editing" class="note-section">
          <h3 class="section-label analysis-label">🔬 Deep Analysis</h3>
          <template v-if="editing">
            <textarea v-model="form.deepAnalysis" class="edit-textarea" rows="8" />
          </template>
          <template v-else>
            <div v-if="article.deep_analysis" class="section-content md-render editable" @click="focusField('deep_analysis')" v-html="renderMd(article.deep_analysis)" />
            <div v-else class="section-content editable placeholder" @click="focusField('deep_analysis')">暂无分析（点击编辑）</div>
          </template>
        </div>
      </div>

      <div class="source-panel">
        <div v-if="article.status === 'failed'" class="unparsable-notice">
          <p>✗ 链接无法访问</p>
          <a :href="article.url" target="_blank" class="open-link">尝试在新标签页打开 →</a>
        </div>
        <div v-else-if="article.status === 'unparsable' && !iframeOk" class="unparsable-notice">
          <p>⚠️ 无法提取正文内容</p>
          <a :href="article.url" target="_blank" class="open-link">在新标签页打开原文 →</a>
        </div>
        <template v-else>
          <iframe v-if="iframeOk" :src="article.url" class="source-iframe" sandbox="allow-same-origin allow-popups" @error="iframeOk = false" />
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
import { marked } from "marked";

const route = useRoute();
const router = useRouter();
const blogStore = useBlogStore();
const article = computed(() => blogStore.currentArticle);
const iframeOk = ref(true);
const editing = ref(false);

marked.setOptions({ breaks: true, gfm: true });

function renderMd(text: string): string {
  return marked.parse(text) as string;
}

const form = ref({
  title: "",
  summary: "",
  keyPointsText: "",
  deepAnalysis: "",
  categoryId: null as number | null,
});

function startEdit() {
  const a = article.value;
  if (!a) return;
  form.value = {
    title: a.title,
    summary: a.summary || "",
    keyPointsText: a.key_points || "",
    deepAnalysis: a.deep_analysis || "",
    categoryId: a.category,
  };
  editing.value = true;
}

function cancelEdit() {
  editing.value = false;
}

function focusField(field: string) {
  startEdit();
}

function editingField(_field: string) {
  return editing.value;
}

async function handleSave() {
  if (!article.value) return;
  await blogStore.updateArticle(article.value.id, {
    title: form.value.title,
    summary: form.value.summary,
    key_points: form.value.keyPointsText,
    deep_analysis: form.value.deepAnalysis,
    category: form.value.categoryId,
  });
  editing.value = false;
}

const scoreClass = computed(() => {
  if (!article.value?.score) return "";
  if (article.value.score >= 7) return "score-high";
  if (article.value.score >= 4) return "score-mid";
  return "score-low";
});

onMounted(() => {
  blogStore.fetchCategories();
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
.save-btn { border-color: #3fb950; color: #3fb950; }
.save-btn:hover { background: rgba(63, 185, 80, 0.1); }
.detail-body { display: flex; flex: 1; overflow: hidden; }
.note-panel { width: 33.33%; border-right: 1px solid var(--border-primary); padding: 24px; overflow-y: auto; }
.article-title { font-size: 20px; color: var(--text-primary); margin-bottom: 12px; line-height: 1.4; }
.article-meta { display: flex; gap: 12px; align-items: center; margin-bottom: 20px; font-size: 13px; color: var(--text-secondary); flex-wrap: wrap; }
.article-meta a { color: var(--accent); }
.category-badge { cursor: pointer; padding: 2px 8px; border-radius: 12px; background: rgba(110,118,129,0.1); transition: background 0.15s; }
.category-badge:hover { background: rgba(110,118,129,0.2); }
.category-select { padding: 4px 8px; background: var(--input-bg); border: 1px solid var(--accent); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px; outline: none; }
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

/* Editable fields */
.editable {
  cursor: text;
  border-radius: 4px;
  padding: 2px 4px;
  margin: -2px -4px;
  transition: background 0.15s;
}
.editable:hover { background: rgba(110, 118, 129, 0.1); }
.placeholder { color: var(--text-muted); font-style: italic; }
.edit-input, .edit-textarea {
  width: 100%; background: var(--bg-primary); border: 1px solid var(--accent);
  border-radius: var(--radius-sm); color: var(--text-primary);
  font-size: 14px; padding: 8px 10px; line-height: 1.6;
  font-family: inherit; resize: vertical; outline: none;
}
.title-input { font-size: 20px; font-weight: 700; margin-bottom: 12px; padding: 6px 10px; }

/* Markdown rendered content */
.md-render { font-size: 14px; line-height: 1.8; color: var(--text-primary); word-break: break-word; }
.md-render :deep(h1), .md-render :deep(h2), .md-render :deep(h3),
.md-render :deep(h4), .md-render :deep(h5), .md-render :deep(h6) {
  margin: 16px 0 8px; font-weight: 600; color: var(--text-primary);
}
.md-render :deep(h1) { font-size: 18px; }
.md-render :deep(h2) { font-size: 16px; }
.md-render :deep(h3) { font-size: 15px; }
.md-render :deep(p) { margin: 6px 0; }
.md-render :deep(ul), .md-render :deep(ol) { padding-left: 20px; margin: 6px 0; }
.md-render :deep(li) { margin-bottom: 4px; }
.md-render :deep(strong) { color: var(--text-primary); font-weight: 600; }
.md-render :deep(em) { color: var(--text-secondary); }
.md-render :deep(code) {
  background: rgba(110, 118, 129, 0.15); padding: 2px 6px;
  border-radius: 3px; font-size: 13px; font-family: monospace;
}
.md-render :deep(pre) {
  background: rgba(110, 118, 129, 0.1); padding: 12px;
  border-radius: var(--radius-sm); overflow-x: auto; margin: 8px 0;
}
.md-render :deep(pre code) { background: none; padding: 0; }
.md-render :deep(blockquote) {
  border-left: 3px solid var(--accent); padding-left: 12px;
  margin: 8px 0; color: var(--text-secondary);
}
.md-render :deep(hr) { border: none; border-top: 1px solid var(--border-primary); margin: 12px 0; }
.md-render :deep(table) { border-collapse: collapse; width: 100%; margin: 8px 0; }
.md-render :deep(th), .md-render :deep(td) {
  border: 1px solid var(--border-primary); padding: 6px 10px; text-align: left; font-size: 13px;
}
.md-render :deep(th) { background: rgba(110, 118, 129, 0.08); font-weight: 600; }
</style>
