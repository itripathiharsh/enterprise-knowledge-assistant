"use client";
import { useEffect, useRef } from "react";
import { Message } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { ThinkingIndicator } from "./ThinkingIndicator";

interface Props {
  messages: Message[];
  thinkingStep: number;
  onFollowUp: (q: string) => void;
  sessionId: string;
}

export function ChatWindow({ messages, thinkingStep, onFollowUp, sessionId }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinkingStep]);

  return (
    <div className="flex flex-col gap-6 p-4 pb-2">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} onFollowUp={onFollowUp} sessionId={sessionId} />
      ))}
      {thinkingStep >= 0 && (
        <div className="flex">
          <ThinkingIndicator currentStep={thinkingStep} />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
