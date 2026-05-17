<template>
  <div class="blog-settings">
    <h1>知识笔记设置</h1>
    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key"
        :class="['tab', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key">{{ tab.label }}</button>
    </div>

    <!-- RSS 源 -->
    <div v-if="activeTab === 'rss'" class="tab-content">
      <div class="section-header">
        <h2>RSS 源 ({{ blogStore.rssSources.length }}/{{ rssLimit }})</h2>
        <button class="add-btn" :disabled="blogStore.rssSources.length >= rssLimit" @click="showAddRss = true">+ 添加源</button>
      </div>
      <p v-if="blogStore.rssSources.length >= rssLimit" class="limit-warn">已达上限 {{ rssLimit }} 个</p>
      <table class="data-table">
        <thead><tr><th>名称</th><th>URL</th><th>间隔</th><th>上次抓取</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="src in blogStore.rssSources" :key="src.id">
            <td>{{ src.name }}</td>
            <td class="url-cell">{{ src.url }}</td>
            <td>{{ src.fetch_interval / 60 }}分钟</td>
            <td>{{ src.last_fetched ? formatDate(src.last_fetched) : '—' }}</td>
            <td><button class="del-btn" @click="blogStore.deleteRSSSource(src.id)">删除</button></td>
          </tr>
        </tbody>
      </table>
      <div v-if="showAddRss" class="inline-form">
        <input v-model="newRss.name" placeholder="源名称" class="form-input" />
        <input v-model="newRss.url" placeholder="RSS URL" class="form-input" />
        <select v-model="newRss.category" class="form-select">
          <option :value="null">无分类</option>
          <option v-for="cat in blogStore.categories" :key="cat.id" :value="cat.id">{{ cat.icon }} {{ cat.name }}</option>
        </select>
        <button class="btn-primary" @click="addRss">添加</button>
        <button class="btn-cancel" @click="showAddRss = false">取消</button>
      </div>
    </div>

    <!-- 分类 -->
    <div v-if="activeTab === 'categories'" class="tab-content">
      <div class="section-header">
        <h2>分类管理</h2>
        <button class="add-btn" @click="showAddCat = true">+ 新建分类</button>
      </div>
      <div v-for="cat in blogStore.categories" :key="cat.id" class="cat-item">
        <div class="cat-header">
          <span>{{ cat.icon }} {{ cat.name }}</span>
          <span class="cat-count">{{ cat.article_count }} 篇</span>
          <button class="del-btn" @click="blogStore.deleteCategory(cat.id)">删除</button>
        </div>
        <div class="thresholds">
          <label>低分: <input type="number" class="threshold-input" :value="cat.score_thresholds?.low?.[0]" @change="updateThreshold(cat, 'low', 0, $event)" /> - <input type="number" class="threshold-input" :value="cat.score_thresholds?.low?.[1]" @change="updateThreshold(cat, 'low', 1, $event)" /></label>
          <label>中分: <input type="number" class="threshold-input" :value="cat.score_thresholds?.mid?.[0]" @change="updateThreshold(cat, 'mid', 0, $event)" /> - <input type="number" class="threshold-input" :value="cat.score_thresholds?.mid?.[1]" @change="updateThreshold(cat, 'mid', 1, $event)" /></label>
          <label>高分: <input type="number" class="threshold-input" :value="cat.score_thresholds?.high?.[0]" @change="updateThreshold(cat, 'high', 0, $event)" /> - <input type="number" class="threshold-input" :value="cat.score_thresholds?.high?.[1]" @change="updateThreshold(cat, 'high', 1, $event)" /></label>
        </div>
      </div>
      <div v-if="showAddCat" class="inline-form">
        <input v-model="newCat.name" placeholder="分类名" class="form-input" />
        <input v-model="newCat.icon" placeholder="图标 emoji" class="form-input" />
        <label class="threshold-form-label">低分: <input type="number" v-model.number="newCat.lowMax" class="threshold-input" /></label>
        <label class="threshold-form-label">中分: <input type="number" v-model.number="newCat.midMax" class="threshold-input" /></label>
        <label class="threshold-form-label">高分: <input type="number" v-model.number="newCat.highMax" class="threshold-input" /></label>
        <button class="btn-primary" @click="addCat">创建</button>
        <button class="btn-cancel" @click="showAddCat = false">取消</button>
      </div>
    </div>

    <!-- 评分 -->
    <div v-if="activeTab === 'scoring'" class="tab-content">
      <h2>评分与模型</h2>
      <div class="setting-row"><span>L1 模型（过滤）</span><span class="setting-value">{{ blogStore.config?.l1_model || 'deepseek-chat' }}</span></div>
      <div class="setting-row"><span>L2 模型（深度）</span><span class="setting-value">{{ blogStore.config?.l2_model || 'glm-4-plus' }}</span></div>
      <p class="hint">模型配置后续可在 AI 设置中修改</p>
    </div>

    <!-- 工具 -->
    <div v-if="activeTab === 'tools'" class="tab-content">
      <h2>调度与工具</h2>
      <div class="tool-actions"><button class="action-btn" @click="handleFetchAll">🔄 全量抓取</button></div>
      <h3 style="margin-top:24px">无效链接</h3>
      <table class="data-table">
        <thead><tr><th>URL</th><th>原因</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="f in blogStore.failedUrls" :key="f.id">
            <td class="url-cell">{{ f.url }}</td>
            <td>{{ f.reason }}</td>
            <td><button class="del-btn" @click="blogStore.deleteFailedUrl(f.id)">删除</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useBlogStore } from "@/stores/blog";

const blogStore = useBlogStore();
const activeTab = ref("rss");
const showAddRss = ref(false);
const showAddCat = ref(false);
const newRss = ref({ name: "", url: "", category: null as number | null });
const newCat = ref({ name: "", icon: "📁", lowMax: 3, midMax: 6, highMax: 10 });

const rssLimit = computed(() => blogStore.config?.rss_source_limit || 40);
const tabs = [
  { key: "rss", label: "RSS 源" },
  { key: "categories", label: "分类" },
  { key: "scoring", label: "评分" },
  { key: "tools", label: "工具" },
];

onMounted(async () => {
  await Promise.all([
    blogStore.fetchRSSSources(), blogStore.fetchCategories(),
    blogStore.fetchConfig(), blogStore.fetchFailedUrls(),
  ]);
});

async function addRss() {
  if (!newRss.value.name || !newRss.value.url) return;
  await blogStore.createRSSSource({ name: newRss.value.name, url: newRss.value.url, category: newRss.value.category });
  newRss.value = { name: "", url: "", category: null };
  showAddRss.value = false;
}

async function addCat() {
  if (!newCat.value.name) return;
  const { lowMax, midMax, highMax } = newCat.value;
  await blogStore.createCategory({
    name: newCat.value.name, icon: newCat.value.icon,
    score_thresholds: { low: [1, lowMax], mid: [lowMax + 1, midMax], high: [midMax + 1, highMax] },
  });
  newCat.value = { name: "", icon: "📁", lowMax: 3, midMax: 6, highMax: 10 };
  showAddCat.value = false;
}

function updateThreshold(cat: any, level: string, idx: number, event: Event) {
  const val = Number((event.target as HTMLInputElement).value);
  const t = { ...cat.score_thresholds };
  t[level] = [...t[level]];
  t[level][idx] = val;
  blogStore.updateCategory(cat.id, { score_thresholds: t });
}

async function handleFetchAll() {
  await blogStore.fetchAll();
  blogStore.fetchArticles();
}

function formatDate(dateStr: string) {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString("zh-CN");
}
</script>

<style scoped>
.blog-settings { max-width: 900px; }
.blog-settings h1 { font-size: 24px; color: var(--text-primary); margin-bottom: 20px; }
.tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border-primary); margin-bottom: 20px; }
.tab {
  padding: 10px 20px; background: none; border: none; border-bottom: 2px solid transparent;
  color: var(--text-secondary); cursor: pointer; font-size: 14px;
}
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h2 { font-size: 16px; color: var(--text-primary); }
.add-btn {
  padding: 6px 14px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.add-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.limit-warn { color: var(--warning); font-size: 13px; margin-bottom: 12px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 8px; border-bottom: 1px solid var(--border-primary); color: var(--text-secondary); }
.data-table td { padding: 8px; border-bottom: 1px solid var(--border-secondary); color: var(--text-primary); }
.url-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-btn {
  background: none; border: 1px solid var(--border-primary); border-radius: var(--radius-sm);
  color: var(--error); cursor: pointer; padding: 4px 8px; font-size: 12px;
}
.inline-form { display: flex; gap: 8px; margin-top: 16px; align-items: center; flex-wrap: wrap; }
.form-input, .form-select {
  padding: 8px 10px; background: var(--input-bg); border: 1px solid var(--input-border);
  border-radius: var(--radius-sm); color: var(--text-primary); font-size: 13px;
}
.btn-primary {
  padding: 8px 14px; background: var(--btn-primary-bg); border: none;
  border-radius: var(--radius-sm); color: var(--btn-primary-text); cursor: pointer; font-size: 13px;
}
.btn-cancel {
  padding: 8px 14px; background: none; border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-secondary); cursor: pointer; font-size: 13px;
}
.cat-item {
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: var(--radius-md); padding: 12px 16px; margin-bottom: 8px;
}
.cat-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.cat-count { font-size: 12px; color: var(--text-muted); }
.thresholds { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.threshold-input {
  width: 40px; padding: 4px; text-align: center; background: var(--input-bg);
  border: 1px solid var(--input-border); border-radius: var(--radius-sm); color: var(--text-primary); font-size: 12px;
}
.threshold-form-label { font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px; }
.setting-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border-secondary); }
.setting-value { color: var(--text-primary); }
.hint { font-size: 12px; color: var(--text-muted); margin-top: 12px; }
.tool-actions { margin-bottom: 16px; }
.action-btn {
  padding: 8px 16px; background: var(--card-bg); border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm); color: var(--text-primary); cursor: pointer; font-size: 13px;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }
</style>
