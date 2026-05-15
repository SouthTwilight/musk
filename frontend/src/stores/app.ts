import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/core/api";

export const useAppStore = defineStore("app", () => {
  const sidebarCollapsed = ref(false);
  const theme = ref<"dark" | "light">("dark");
  const backgroundImage = ref("");

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value;
    api.patch("/config/", { sidebar_collapsed: sidebarCollapsed.value });
  }

  function setTheme(t: "dark" | "light") {
    theme.value = t;
    document.documentElement.setAttribute("data-theme", t);
    api.patch("/config/", { theme: t });
  }

  function setBackgroundImage(url: string) {
    backgroundImage.value = url;
    api.patch("/config/", { background_image: url });
  }

  async function loadConfig() {
    try {
      const { data } = await api.get("/config/");
      theme.value = data.theme || "dark";
      sidebarCollapsed.value = data.sidebar_collapsed || false;
      backgroundImage.value = data.background_image || "";
      document.documentElement.setAttribute("data-theme", theme.value);
    } catch {
      // 使用默认值
    }
  }

  return {
    sidebarCollapsed,
    theme,
    backgroundImage,
    toggleSidebar,
    setTheme,
    setBackgroundImage,
    loadConfig,
  };
});
