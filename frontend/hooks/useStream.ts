import { useCallback, useRef } from "react";
import { API_BASE_URL } from "@/lib/constants";
import { Source, ChunkResult } from "@/lib/types";

interface StreamCallbacks {
  onMetadata: (meta: { sources: Source[]; chunks: ChunkResult[]; confidence: number }) => void;
  onText: (text: string) => void;
  onFollowUps: (questions: string[]) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export function useStream() {
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(async (
    question: string,
    session_id: string,
    callbacks: StreamCallbacks,
    doc_filter?: string[]
  ) => {
    abortRef.current = new AbortController();

    try {
      const token = localStorage.getItem("auth_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;

      const response = await fetch(`${API_BASE_URL}/ask/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({ question, session_id, doc_filter }),
        signal: abortRef.current.signal
      });

      if (!response.ok) {
        let errMsg = "Stream request failed";
        try {
          const errData = await response.json();
          errMsg = errData.detail || errMsg;
        } catch {}
        throw new Error(errMsg);
      }
      
      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "metadata") callbacks.onMetadata(data);
              else if (data.type === "text") callbacks.onText(data.content);
              else if (data.type === "follow_ups") callbacks.onFollowUps(data.questions);
              else if (data.type === "done") callbacks.onDone();
            } catch {}
          }
        }
      }
    } catch (error: any) {
      if (error.name !== "AbortError") {
        callbacks.onError(error.message);
      }
    }
  }, []);

  const abort = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { stream, abort };
}
