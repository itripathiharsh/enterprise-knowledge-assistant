"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { Message, Source, ChunkResult } from "@/lib/types";
import { useStream } from "./useStream";
import { THINKING_STEPS } from "@/lib/constants";
import { getChatHistory, api } from "@/lib/api";

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState<number>(-1);
  const { stream, abort } = useStream();
  const thinkingInterval = useRef<NodeJS.Timeout>();

  const getSessionId = useCallback(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("auth_user_id") || uuidv4();
    }
    return uuidv4();
  }, []);

  const sessionId = useRef(getSessionId());

  useEffect(() => {
    sessionId.current = getSessionId();
    const loadHistory = async () => {
      try {
        const history = await getChatHistory();
        if (history && history.length > 0) {
          const formattedMessages: Message[] = history.map((msg, i) => ({
            id: `history-${i}`,
            role: msg.role as "user" | "assistant",
            content: msg.content,
            timestamp: new Date(),
            isStreaming: false
          }));
          setMessages(formattedMessages);
        }
      } catch (err) {
        console.error("Failed to load chat history", err);
      }
    };
    if (localStorage.getItem("auth_token")) {
      loadHistory();
    }
  }, [getSessionId]);

  const startThinkingAnimation = useCallback(() => {
    let step = 0;
    setThinkingStep(0);
    const advance = () => {
      step++;
      if (step < THINKING_STEPS.length - 1) {
        setThinkingStep(step);
        const duration = THINKING_STEPS[step].duration;
        if (duration > 0) {
          thinkingInterval.current = setTimeout(advance, duration);
        }
        // Last thinking step stays until stream starts
      }
    };
    thinkingInterval.current = setTimeout(advance, THINKING_STEPS[0].duration);
  }, []);

  const stopThinkingAnimation = useCallback(() => {
    if (thinkingInterval.current) clearTimeout(thinkingInterval.current);
    setThinkingStep(-1);
  }, []);

  const sendMessage = useCallback(async (
    question: string,
    docFilter?: string[]
  ) => {
    if (!question.trim() || isLoading) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      content: question,
      timestamp: new Date()
    };

    const assistantMsgId = uuidv4();
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    startThinkingAnimation();

    let metaReceived = false;

    await stream(question, sessionId.current, {
      onMetadata: (meta) => {
        metaReceived = true;
        stopThinkingAnimation();
        setThinkingStep(THINKING_STEPS.length - 1); // "Generating..."
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, sources: meta.sources, chunks: meta.chunks, confidence: meta.confidence }
            : m
        ));
      },
      onText: (text) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: m.content + text }
            : m
        ));
      },
      onFollowUps: (questions) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, followUpQuestions: questions }
            : m
        ));
      },
      onDone: () => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, isStreaming: false }
            : m
        ));
        stopThinkingAnimation();
        setIsLoading(false);
      },
      onError: (error) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantMsgId
            ? { ...m, content: error || "Sorry, something went wrong. Please try again.", isStreaming: false }
            : m
        ));
        stopThinkingAnimation();
        setIsLoading(false);
      }
    }, docFilter);
  }, [isLoading, stream, startThinkingAnimation, stopThinkingAnimation]);

  const clearChat = useCallback(async () => {
    try {
      await api.delete('/query/history');
      setMessages([]);
    } catch (e) {
      console.error("Failed to clear chat", e);
    }
  }, []);

  return {
    messages,
    isLoading,
    thinkingStep,
    sendMessage,
    clearChat,
    sessionId: sessionId.current
  };
}
