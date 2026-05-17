import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/core/api";

export interface Category {
  id: number;
  name: string;
  icon: string;
  score_thresholds: { low: number[]; mid: number[]; high: number[] };
  article_count: number;
}

export interface RSSSource {
  id: number;
  name: string;
  url: string;
  category: number | null;
  fetch_interval: number;
  last_fetched: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Article {
  id: number;
  title: string;
  url: string;
  category: number | null;
  category_name: string;
  category_icon: string;
  status: string;
  score: number | null;
  source_name: string;
  summary: string;
  key_points: string;
  deep_analysis: string;
  raw_text: string;
  published_at: string | null;
  created_at: string;
}

export interface BlogConfig {
  l1_model: string;
  l2_model: string;
  rss_source_limit: number;
  default_score_dims: string[];
  [key: string]: unknown;
}

export const useBlogStore = defineStore("blog", () => {
  const categories = ref<Category[]>([]);
  const rssSources = ref<RSSSource[]>([]);
  const articles = ref<Article[]>([]);
  const currentArticle = ref<Article | null>(null);
  const config = ref<BlogConfig | null>(null);
  const loading = ref(false);
  const failedUrls = ref<{ id: number; url: string; reason: string }[]>([]);

  async function fetchCategories() {
    const { data } = await api.get("/blog/categories/");
    categories.value = data;
  }

  async function createCategory(payload: Partial<Category>) {
    const { data } = await api.post("/blog/categories/", payload);
    categories.value.push(data);
    return data;
  }

  async function updateCategory(id: number, payload: Partial<Category>) {
    const { data } = await api.put(`/blog/categories/${id}/`, payload);
    const idx = categories.value.findIndex((c) => c.id === id);
    if (idx !== -1) categories.value[idx] = data;
    return data;
  }

  async function deleteCategory(id: number) {
    await api.delete(`/blog/categories/${id}/`);
    categories.value = categories.value.filter((c) => c.id !== id);
  }

  async function fetchRSSSources() {
    const { data } = await api.get("/blog/rss-sources/");
    rssSources.value = data;
  }

  async function createRSSSource(payload: Partial<RSSSource>) {
    const { data } = await api.post("/blog/rss-sources/", payload);
    rssSources.value.push(data);
    return data;
  }

  async function updateRSSSource(id: number, payload: Partial<RSSSource>) {
    const { data } = await api.put(`/blog/rss-sources/${id}/`, payload);
    const idx = rssSources.value.findIndex((s) => s.id === id);
    if (idx !== -1) rssSources.value[idx] = data;
    return data;
  }

  async function deleteRSSSource(id: number) {
    await api.delete(`/blog/rss-sources/${id}/`);
    rssSources.value = rssSources.value.filter((s) => s.id !== id);
  }

  async function fetchArticles(params?: Record<string, string>) {
    loading.value = true;
    try {
      const { data } = await api.get("/blog/articles/", { params });
      articles.value = data;
    } finally {
      loading.value = false;
    }
  }

  async function fetchArticle(id: number) {
    const { data } = await api.get(`/blog/articles/${id}/`);
    currentArticle.value = data;
    return data;
  }

  async function fetchUrl(url: string, categoryId?: number) {
    const { data } = await api.post("/blog/articles/fetch_url/", {
      url,
      category_id: categoryId,
    });
    return data;
  }

  async function reprocessArticle(id: number) {
    const { data } = await api.post(`/blog/articles/${id}/reprocess/`);
    return data;
  }

  async function deleteArticle(id: number) {
    await api.delete(`/blog/articles/${id}/`);
    articles.value = articles.value.filter((a) => a.id !== id);
  }

  async function updateArticle(id: number, payload: Partial<Article>) {
    const { data } = await api.patch(`/blog/articles/${id}/`, payload);
    if (currentArticle.value?.id === id) currentArticle.value = data;
    const idx = articles.value.findIndex((a) => a.id === id);
    if (idx !== -1) articles.value[idx] = data;
    return data;
  }

  async function exportArticle(id: number) {
    const { data } = await api.post(
      `/blog/articles/${id}/export/`,
      {},
      { responseType: "blob" }
    );
    return data;
  }

  async function fetchConfig() {
    const { data } = await api.get("/blog/config/");
    config.value = data;
    return data;
  }

  async function updateConfig(payload: Record<string, unknown>) {
    const { data } = await api.put("/blog/config/", payload);
    return data;
  }

  async function fetchFailedUrls() {
    const { data } = await api.get("/blog/failed-urls/");
    failedUrls.value = data;
  }

  async function deleteFailedUrl(id: number) {
    await api.delete(`/blog/failed-urls/${id}/`);
    failedUrls.value = failedUrls.value.filter((f) => f.id !== id);
  }

  async function fetchAll() {
    const { data } = await api.post("/blog/scheduler/fetch_all/");
    return data;
  }

  return {
    categories, rssSources, articles, currentArticle,
    config, loading, failedUrls,
    fetchCategories, createCategory, updateCategory, deleteCategory,
    fetchRSSSources, createRSSSource, updateRSSSource, deleteRSSSource,
    fetchArticles, fetchArticle, fetchUrl, reprocessArticle,
    deleteArticle, updateArticle, exportArticle,
    fetchConfig, updateConfig,
    fetchFailedUrls, deleteFailedUrl,
    fetchAll,
  };
});