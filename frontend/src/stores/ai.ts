import { defineStore } from "pinia";
import { ref } from "vue";
import api from "@/core/api";

export interface Conversation {
  id: number;
  title: string;
  model_name: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface PromptTemplate {
  id: number;
  name: string;
  prompt: string;
  variables: string[];
  category: string;
  module: string;
}

export const useAiStore = defineStore("ai", () => {
  const conversations = ref<Conversation[]>([]);
  const currentConversationId = ref<number | null>(null);
  const messages = ref<ChatMessage[]>([]);
  const templates = ref<PromptTemplate[]>([]);
  const loading = ref(false);
  const streamingContent = ref("");

  async function fetchConversations() {
    const { data } = await api.get("/ai/conversations/");
    conversations.value = data;
  }

  async function fetchConversation(id: number) {
    const { data } = await api.get(`/ai/conversations/${id}/`);
    currentConversationId.value = id;
    messages.value = data.messages || [];
  }

  async function createConversation(title: string = "新对话") {
    const { data } = await api.post("/ai/conversations/", { title });
    conversations.value.unshift(data);
    currentConversationId.value = data.id;
    messages.value = [];
    return data;
  }

  async function deleteConversation(id: number) {
    await api.delete(`/ai/conversations/${id}/`);
    conversations.value = conversations.value.filter((c) => c.id !== id);
    if (currentConversationId.value === id) {
      currentConversationId.value = null;
      messages.value = [];
    }
  }

  async function sendMessage(content: string, useStream: boolean = true) {
    loading.value = true;
    streamingContent.value = "";

    // 添加用户消息到 UI
    messages.value.push({ role: "user", content });

    try {
      if (useStream) {
        // SSE 流式
        const token = localStorage.getItem("access");
        const body = JSON.stringify({
          message: content,
          conversation_id: currentConversationId.value,
          model: "deepseek",
        });

        const response = await fetch("/api/ai/chat/?stream=true", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body,
        });

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let fullContent = "";

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value, { stream: true });
            const lines = text.split("\n");

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.slice(6));
                  if (data.content) {
                    fullContent += data.content;
                    streamingContent.value = fullContent;
                  }
                  if (data.done) {
                    currentConversationId.value = data.conversation_id;
                  }
                } catch {
                  // skip
                }
              }
            }
          }
        }

        messages.value.push({ role: "assistant", content: fullContent });
        streamingContent.value = "";
      } else {
        // 普通请求
        const { data } = await api.post("/ai/chat/", {
          message: content,
          conversation_id: currentConversationId.value,
          model: "deepseek",
        });
        messages.value.push(data.message);
        currentConversationId.value = data.conversation_id;
      }
    } catch (e) {
      messages.value.push({
        role: "assistant",
        content: "抱歉，AI 调用失败，请检查 API Key 配置。",
      });
    } finally {
      loading.value = false;
    }
  }

  async function fetchTemplates() {
    const { data } = await api.get("/ai/templates/");
    templates.value = data;
  }

  function newChat() {
    currentConversationId.value = null;
    messages.value = [];
  }

  return {
    conversations,
    currentConversationId,
    messages,
    templates,
    loading,
    streamingContent,
    fetchConversations,
    fetchConversation,
    createConversation,
    deleteConversation,
    sendMessage,
    fetchTemplates,
    newChat,
  };
});
