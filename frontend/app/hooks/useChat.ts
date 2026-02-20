"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import type { Message, Source, SSEChunk } from "../lib/types";

const STORAGE_KEY = "aoe4bot_chat_history";
const MAX_STORED_MESSAGES = 50;

let nextId = 0;
function genId() {
  return `msg_${Date.now()}_${nextId++}`;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return parsed.map((m: Message) => ({ ...m, activeTools: undefined }));
      }
    } catch {}
    return [];
  });
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  // Persist to localStorage
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const toStore = messages.slice(-MAX_STORED_MESSAGES).map(
        ({ activeTools: _, ...m }) => m
      );
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
    } catch {}
  }, [messages]);

  const sendMessage = useCallback(async (text: string) => {
    const userMsg: Message = { id: genId(), role: "user", content: text };
    const assistantMsg: Message = { id: genId(), role: "assistant", content: "" };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);

    // Build message history for API
    const history = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content,
    }));

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history, stream: true }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: "Error connecting to the server. Please try again." }
              : m
          )
        );
        setIsLoading(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accContent = "";
      let accSources: Source[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE events
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.slice(5).trim();
          if (!jsonStr || jsonStr === "[DONE]") continue;

          try {
            const chunk: SSEChunk = JSON.parse(jsonStr);

            if (chunk.type === "token" && chunk.content) {
              accContent += chunk.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id
                    ? { ...m, content: accContent, activeTools: undefined }
                    : m
                )
              );
            } else if (chunk.type === "tool_call" && chunk.content) {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id
                    ? { ...m, activeTools: [...(m.activeTools || []), chunk.content!] }
                    : m
                )
              );
            } else if (chunk.type === "sources" && chunk.sources) {
              accSources = chunk.sources;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id ? { ...m, sources: accSources } : m
                )
              );
            } else if (chunk.type === "done") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id ? { ...m, activeTools: undefined } : m
                )
              );
            } else if (chunk.type === "error" && chunk.content) {
              accContent += `\n\n*Error: ${chunk.content}*`;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsg.id ? { ...m, content: accContent } : m
                )
              );
            }
          } catch {
            // Skip malformed JSON
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== "AbortError") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? { ...m, content: "Connection lost. Please try again." }
              : m
          )
        );
      }
    } finally {
      setIsLoading(false);
      abortRef.current = null;
    }
  }, [messages]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const resetChat = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsLoading(false);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }, []);

  return { messages, isLoading, sendMessage, stop, resetChat };
}
