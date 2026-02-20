"use client";

import { useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import Header from "./Header";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import WelcomeScreen from "./WelcomeScreen";

export default function ChatInterface() {
  const { messages, isLoading, sendMessage, stop, resetChat } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Find the last assistant message index
  const lastAssistantIdx = messages.reduce(
    (acc, msg, i) => (msg.role === "assistant" ? i : acc),
    -1
  );

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header onLogoClick={resetChat} />
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeScreen onSelect={sendMessage} />
        ) : (
          <div className="max-w-4xl mx-auto px-4 py-6">
            {messages.map((msg, i) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                isLatest={i === lastAssistantIdx && !isLoading}
                onFollowUp={sendMessage}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <ChatInput onSend={sendMessage} isLoading={isLoading} onStop={stop} />
    </div>
  );
}
