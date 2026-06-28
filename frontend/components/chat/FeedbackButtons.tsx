"use client";
import { useState } from "react";
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { submitFeedback } from "@/lib/api";

interface Props { sessionId: string; question: string; answer: string; }

export function FeedbackButtons({ sessionId, question, answer }: Props) {
  const [sent, setSent] = useState<"helpful" | "not_helpful" | null>(null);

  const handleFeedback = async (type: "helpful" | "not_helpful") => {
    if (sent) return;
    setSent(type);
    try {
      await submitFeedback({ session_id: sessionId, question, answer, feedback: type });
    } catch {}
  };

  return (
    <div className="flex items-center gap-1">
      <button onClick={() => handleFeedback("helpful")}
        className={`p-1 rounded transition-colors ${sent === "helpful" ? "text-green-500" : "text-muted-foreground hover:text-foreground"}`}>
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>
      <button onClick={() => handleFeedback("not_helpful")}
        className={`p-1 rounded transition-colors ${sent === "not_helpful" ? "text-red-500" : "text-muted-foreground hover:text-foreground"}`}>
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
