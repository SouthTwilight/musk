<template>
  <div class="ai-chat">
    <div class="chat-sidebar">
      <button class="new-chat-btn" @click="aiStore.newChat()">+ 新对话</button>
      <div class="conversation-list">
        <div
          v-for="conv in aiStore.conversations"
          :key="conv.id"
          :class="['conv-item', { active: aiStore.currentConversationId === conv.id }]"
          @click="aiStore.fetchConversation(conv.id)"
        >
          <span class="conv-title">{{ conv.title }}</span>
          <button class="conv-delete" @click.stop="aiStore.deleteConversation(conv.id)">×</button>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div class="messages" ref="messagesRef">
        <div
          v-for="(msg, i) in aiStore.messages"
          :key="i"
          :class="['message', msg.role]"
        >
          <div class="message-content">{{ msg.content }}</div>
        </div>
        <div v-if="aiStore.streamingContent" class="message assistant">
          <div class="message-content streaming">{{ aiStore.streamingContent }}▊</div>
        </div>
        <div v-if="aiStore.messages.length === 0 && !aiStore.loading" class="empty-state">
          <div class="empty-icon">🤖</div>
          <h3>AI 助手</h3>
          <p>输入消息开始对话</p>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="inputText"
          class="chat-input"
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          rows="2"
          @keydown.enter.exact.prevent="handleSend"
          :disabled="aiStore.loading"
        />
        <button class="send-btn" @click="handleSend" :disabled="aiStore.loading || !inputText.trim()">
          {{ aiStore.loading ? '...' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from "vue";
import { useAiStore } from "@/stores/ai";

const aiStore = useAiStore();
const inputText = ref("");
const messagesRef = ref<HTMLElement>();

onMounted(() => {
  aiStore.fetchConversations();
  aiStore.fetchTemplates();
});

watch(
  () => [aiStore.messages.length, aiStore.streamingContent],
  () => {
    nextTick(() => {
      if (messagesRef.value) {
        messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
      }
    });
  }
);

function handleSend() {
  const text = inputText.value.trim();
  if (!text || aiStore.loading) return;
  inputText.value = "";
  aiStore.sendMessage(text, true);
}
</script>

<style scoped>
.ai-chat {
  display: flex;
  height: calc(100vh - 52px - 48px);
  margin: -24px;
}

.chat-sidebar {
  width: 240px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-primary);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.new-chat-btn {
  margin: 12px;
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.15s;
}

.new-chat-btn:hover { opacity: 0.9; }

.conversation-list { flex: 1; overflow-y: auto; padding: 0 8px; }

.conv-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.15s;
}

.conv-item:hover { background: var(--bg-tertiary); color: var(--text-primary); }
.conv-item.active { background: var(--accent-muted, rgba(88,166,255,0.15)); color: var(--accent); }

.conv-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.conv-delete {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  padding: 0 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.conv-item:hover .conv-delete { opacity: 1; }
.conv-delete:hover { color: var(--error); }

.chat-main { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-state h3 { font-size: 18px; color: var(--text-secondary); margin-bottom: 4px; }
.empty-state p { font-size: 13px; }

.message { max-width: 80%; }

.message.user { align-self: flex-end; }
.message.user .message-content {
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-md) var(--radius-md) 4px var(--radius-md);
}

.message.assistant { align-self: flex-start; }
.message.assistant .message-content {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
}

.message-content {
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.streaming { opacity: 0.9; }

.input-area {
  padding: 12px 20px;
  border-top: 1px solid var(--border-primary);
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  resize: none;
  outline: none;
  transition: border-color 0.15s;
}

.chat-input:focus { border-color: var(--accent); }

.send-btn {
  padding: 10px 20px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 14px;
  transition: opacity 0.15s;
}

.send-btn:hover:not(:disabled) { opacity: 0.9; }
.send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
