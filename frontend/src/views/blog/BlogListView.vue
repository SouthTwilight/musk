<template>
  <div class="blog-list">
    <div class="list-header">
      <h1>知识笔记</h1>
      <button class="add-btn" @click="showAddUrl = true">+ 添加链接</button>
    </div>

    <div class="filter-bar">
      <button :class="['filter-chip', { active: activeFilter === 'all' }]" @click="setFilter('all')">全部</button>
      <button v-for="cat in blogStore.categories" :key="cat.id"
        :class="['filter-chip', { active: activeFilter === String(cat.id) }]"
        @click="setFilter(String(cat.id))">{{ cat.icon }} {{ cat.name }}</button>
      <button :class="['filter-chip high-value', { active: activeFilter === 'high' }]" @click="setFilter('high')">⭐ 7+ 高价值</button>
    </div>

    <div v-if="blogStore.loading" class="loading">加载中...</div>
    <div v-else-if="blogStore.articles.length === 0" class="empty">
      <p>暂无文章</p>
      <p class="empty-hint">添加 RSS 源或手动粘贴 URL 开始</p>
    </div>
    <div v-else class="waterfall">
      <div v-for="article in blogStore.articles" :key="article.id"
        :class="['article-card', { 'low-score': article.score && article.score <= 3 }]"
        @click="goDetail(article.id)">
        <div class="card-header">
          <span class="card-meta">{{ article.category_icon }} {{ article.category_name }}</span>
          <span v-if="article.score" class="card-score" :class="scoreClass(article.score)">⭐ {{ article.score }}</span>
        </div>
        <h3 class="card-title">{{ article.title }}</h3>
        <p class="card-summary">{{ article.summary?.slice(0, 80) || '暂无总结' }}</p>
        <div class="card-footer">
          <span class="card-source">{{ article.source_name }}</span>
          <span class="card-date">{{ formatDate(article.created_at) }}</span>
        </div>
      </div>
    </div>

    <AddUrlDialog :visible="showAddUrl" @close="showAddUrl = false" @fetched="onFetched" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useBlogStore } from "@/stores/blog";
import AddUrlDialog from "./AddUrlDialog.vue";

const router = useRouter();
const blogStore = useBlogStore();
const activeFilter = ref("all");
const showAddUrl = ref(false);

onMounted(async () => {
  await Promise.all([blogStore.fetchCategories(), blogStore.fetchArticles()]);
});

function setFilter(filter: string) {
  activeFilter.value = filter;
  if (filter === "all") blogStore.fetchArticles();
  else if (filter === "high") blogStore.fetchArticles({ score_min: "7" });
  else blogStore.fetchArticles({ category: filter });
}

function goDetail(id: number) { router.push(`/blog/${id}`); }
function onFetched() { blogStore.fetchArticles(); }

function scoreClass(score: number) {
  if (score >= 7) return "score-high";
  if (score >= 4) return "score-mid";
  return "score-low";
}

function formatDate(dateStr: string) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}
</script>

<style scoped>
.blog-list { padding: 0 0 24px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.list-header h1 { font-size: 24px; color: var(--text-primary); }
.add-btn {
  padding: 8px 16px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.filter-bar { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-chip {
  padding: 6px 14px; background: transparent; border: 1px solid var(--border-primary);
  border-radius: 20px; color: var(--text-secondary); cursor: pointer; font-size: 13px; transition: all 0.15s;
}
.filter-chip.active { background: var(--accent-muted); border-color: var(--accent); color: var(--accent); }
.filter-chip.high-value.active { background: rgba(188, 140, 255, 0.15); border-color: #bc8cff; color: #bc8cff; }
.waterfall { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.article-card {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-md); padding: 16px; cursor: pointer; transition: all 0.2s;
}
.article-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: var(--card-shadow); }
.article-card.low-score { opacity: 0.6; }
.card-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.card-meta { font-size: 12px; color: var(--text-secondary); }
.card-score { font-size: 12px; font-weight: 600; }
.score-high { color: #bc8cff; }
.score-mid { color: var(--accent); }
.score-low { color: var(--text-muted); }
.card-title { font-size: 15px; color: var(--text-primary); margin-bottom: 6px; line-height: 1.4; }
.card-summary { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.card-footer { display: flex; justify-content: space-between; margin-top: 12px; font-size: 11px; color: var(--text-muted); }
.loading, .empty { text-align: center; padding: 60px 0; color: var(--text-secondary); }
.empty-hint { font-size: 13px; color: var(--text-muted); margin-top: 8px; }
</style>
