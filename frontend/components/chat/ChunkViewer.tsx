"use client";
import { ChunkResult } from "@/lib/types";
import { useState } from "react";
import { ChevronDown, ChevronRight, FileText } from "lucide-react";

interface Props { chunks: ChunkResult[] }

export function ChunkViewer({ chunks }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-muted-foreground hover:bg-muted/50 transition-colors"
      >
        {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        <FileText className="w-3.5 h-3.5" />
        View {chunks.length} retrieved chunks
      </button>
      {open && (
        <div className="border-t border-border divide-y divide-border">
          {chunks.map((chunk, i) => (
            <div key={i} className="px-3 py-2.5">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-medium text-primary">
                  {chunk.doc_name} — Page {chunk.page_number}
                </span>
                <span className="text-xs text-muted-foreground">
                  {(chunk.similarity_score * 100).toFixed(0)}% match
                </span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-4">
                {chunk.text}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
