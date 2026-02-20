"use client";

import { useState, useRef, useEffect } from "react";

interface Props {
  onSend: (text: string) => void;
  isLoading: boolean;
  onStop: () => void;
}

export default function ChatInput({ onSend, isLoading, onStop }: Props) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    }
  }, [text]);

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border bg-bg-dark/80 backdrop-blur-sm p-4">
      <div className="max-w-4xl mx-auto flex gap-3 items-end">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about AoE4..."
          rows={1}
          className="flex-1 resize-none rounded-lg bg-bg-card border border-border
                     text-text-primary placeholder-text-dim text-sm px-4 py-3
                     focus:outline-none focus:border-border-gold transition-colors
                     font-[family-name:var(--font-body)]"
        />
        {isLoading ? (
          <button
            onClick={onStop}
            className="px-5 py-3 rounded-lg bg-[rgba(239,68,68,0.15)] border border-[rgba(239,68,68,0.3)] text-[#f87171]
                       text-sm font-[family-name:var(--font-heading)] font-semibold uppercase tracking-wider
                       hover:bg-[rgba(239,68,68,0.25)] transition-colors cursor-pointer"
          >
            Stop
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!text.trim()}
            className="btn-gold px-5 py-3 rounded-lg text-sm
                       disabled:opacity-20 disabled:cursor-not-allowed disabled:filter-none"
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}
