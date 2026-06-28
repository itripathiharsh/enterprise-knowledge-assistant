"use client";
import { useState } from "react";
import { DocumentInfo } from "@/lib/types";
import { FileText, Trash2, Sparkles, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { summarizeDocument } from "@/lib/api";

interface Props {
  doc: DocumentInfo;
  isSelected: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

export function DocumentCard({ doc, isSelected, onSelect, onDelete }: Props) {
  const [summary, setSummary] = useState("");
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  const handleSummarize = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (summary) { setShowSummary(!showSummary); return; }
    setLoadingSummary(true);
    try {
      const s = await summarizeDocument(doc.doc_id);
      setSummary(s);
      setShowSummary(true);
    } catch {}
    setLoadingSummary(false);
  };

  return (
    <div className={`rounded-xl border transition-colors cursor-pointer
      ${isSelected ? "border-primary bg-primary/5" : "border-border hover:border-primary/30"}`}
      onClick={onSelect}>
      <div className="flex items-start gap-2.5 p-2.5">
        <FileText className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{doc.doc_name}</p>
          <p className="text-xs text-muted-foreground">
            {doc.total_pages}p · {doc.total_chunks} chunks · {doc.file_size_kb.toFixed(0)}KB
          </p>
        </div>
        <div className="flex gap-1 flex-shrink-0">
          <button onClick={handleSummarize} title="Summarize"
            className="p-1 text-muted-foreground hover:text-primary transition-colors">
            {loadingSummary ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
          </button>
          <button onClick={(e) => { e.stopPropagation(); onDelete(); }} title="Delete"
            className="p-1 text-muted-foreground hover:text-destructive transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
      {showSummary && summary && (
        <div className="px-2.5 pb-2.5 text-xs text-muted-foreground border-t border-border pt-2">
          {summary}
        </div>
      )}
    </div>
  );
}
