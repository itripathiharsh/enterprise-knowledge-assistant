"use client";
import { Message } from "@/lib/types";
import { SourceCard } from "./SourceCard";
import { ChunkViewer } from "./ChunkViewer";
import { FeedbackButtons } from "./FeedbackButtons";
import { FollowUpSuggestions } from "./FollowUpSuggestions";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { LOW_CONFIDENCE_THRESHOLD } from "@/lib/constants";

interface Props {
  message: Message;
  onFollowUp: (question: string) => void;
  sessionId: string;
}

export function MessageBubble({ message, onFollowUp, sessionId }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-primary text-primary-foreground px-4 py-3">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  const isLowConfidence = message.confidence !== undefined && message.confidence < LOW_CONFIDENCE_THRESHOLD;

  return (
    <div className="flex flex-col gap-3 max-w-[85%]">
      {/* Answer */}
      <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        {isLowConfidence && (
          <div className="mb-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 rounded-lg px-3 py-1.5">
            ⚠️ Low confidence ({(message.confidence! * 100).toFixed(0)}%) — verify with source documents.
          </div>
        )}
        <p className="text-sm whitespace-pre-wrap leading-relaxed">
          {message.content}
          {message.isStreaming && <span className="inline-block w-0.5 h-4 bg-current ml-0.5 animate-pulse" />}
        </p>
      </div>

      {/* Sources */}
      {message.sources && message.sources.length > 0 && !message.isStreaming && (
        <div className="flex flex-col gap-1.5">
          <p className="text-xs text-muted-foreground font-medium px-1">Sources</p>
          <div className="flex flex-wrap gap-2">
            {message.sources.map((source, i) => (
              <SourceCard key={i} source={source} />
            ))}
          </div>
        </div>
      )}

      {/* Confidence */}
      {message.confidence !== undefined && !message.isStreaming && (
        <div className="flex items-center gap-2 px-1">
          <div className="flex-1 h-1 bg-border rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full transition-all"
              style={{ width: `${message.confidence * 100}%`,
                backgroundColor: message.confidence > 0.6 ? '#22c55e' :
                                  message.confidence > 0.3 ? '#f59e0b' : '#ef4444' }}
            />
          </div>
          <span className="text-xs text-muted-foreground">
            {(message.confidence * 100).toFixed(0)}% match
          </span>
        </div>
      )}

      {/* Retrieved Chunks */}
      {message.chunks && message.chunks.length > 0 && !message.isStreaming && (
        <ChunkViewer chunks={message.chunks} />
      )}

      {/* Actions */}
      {!message.isStreaming && (
        <div className="flex items-center gap-2 px-1">
          <button onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
            {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? "Copied!" : "Copy"}
          </button>
          <FeedbackButtons
            sessionId={sessionId}
            question=""
            answer={message.content}
          />
        </div>
      )}

      {/* Follow-up suggestions */}
      {message.followUpQuestions && message.followUpQuestions.length > 0 && !message.isStreaming && (
        <FollowUpSuggestions questions={message.followUpQuestions} onSelect={onFollowUp} />
      )}
    </div>
  );
}
