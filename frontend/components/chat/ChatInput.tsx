"use client";
import { useState } from "react";
import { Send } from "lucide-react";

interface Props {
  onSend: (q: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, isLoading, disabled, placeholder }: Props) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || isLoading || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        placeholder={placeholder || "Ask a question..."}
        disabled={disabled || isLoading}
        rows={1}
        className="flex-1 resize-none px-4 py-3 rounded-xl border border-border bg-background text-sm
                   outline-none focus:ring-2 focus:ring-primary/30 disabled:opacity-50
                   min-h-[48px] max-h-[160px] overflow-y-auto"
        style={{ height: "48px" }}
        onInput={(e) => {
          const t = e.target as HTMLTextAreaElement;
          t.style.height = "48px";
          t.style.height = Math.min(t.scrollHeight, 160) + "px";
        }}
      />
      <button onClick={handleSend} disabled={disabled || isLoading || !value.trim()}
        className="p-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90
                   disabled:opacity-40 transition-colors flex-shrink-0">
        <Send className="w-4 h-4" />
      </button>
    </div>
  );
}
