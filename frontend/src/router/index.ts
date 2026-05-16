import { createRouter, createWebHistory } from "vue-router";
import LoginView from "@/views/LoginView.vue";
import AppLayout from "@/shell/AppLayout.vue";
import HomeView from "@/views/HomeView.vue";
import SettingsView from "@/views/SettingsView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { requiresAuth: false },
    },
    {
      path: "/",
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: "",
          name: "home",
          component: HomeView,
        },
        {
          path: "settings",
          name: "settings",
          component: SettingsView,
        },
        {
          path: "ai",
          name: "ai",
          component: () => import("@/views/AiChatView.vue"),
        },
        {
          path: "blog",
          children: [
            { path: "", name: "blog", component: () => import("@/views/blog/BlogListView.vue") },
            { path: "settings", name: "blog-settings", component: () => import("@/views/blog/settings/BlogSettingsView.vue") },
            { path: ":id", name: "blog-article", component: () => import("@/views/blog/ArticleDetailView.vue") },
          ],
        },
      ],
    },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("access");
  const isAuthenticated = !!token;

  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: "login" };
  }

  if (to.name === "login" && isAuthenticated) {
    return { name: "home" };
  }
});

export default router;
