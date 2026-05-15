import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/core/api";

interface User {
  id: number;
  username: string;
  email: string;
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const isAuthenticated = ref(false);

  async function register(username: string, email: string, password: string) {
    const response = await api.post("/auth/register/", {
      username,
      email,
      password,
    });

    const { access, refresh } = response.data;
    localStorage.setItem("access", access);
    localStorage.setItem("refresh", refresh);
    isAuthenticated.value = true;

    await fetchUser();
  }

  async function login(username: string, password: string) {
    const response = await api.post("/auth/login/", {
      username,
      password,
    });

    const { access, refresh } = response.data;
    localStorage.setItem("access", access);
    localStorage.setItem("refresh", refresh);
    isAuthenticated.value = true;

    await fetchUser();
  }

  async function fetchUser() {
    try {
      const response = await api.get("/auth/me/");
      user.value = response.data;
      isAuthenticated.value = true;
    } catch {
      user.value = null;
      isAuthenticated.value = false;
    }
  }

  function logout() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    user.value = null;
    isAuthenticated.value = false;
  }

  return {
    user,
    isAuthenticated,
    register,
    login,
    fetchUser,
    logout,
  };
});
