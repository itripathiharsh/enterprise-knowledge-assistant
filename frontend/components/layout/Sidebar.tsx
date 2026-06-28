"use client";
import { DocumentInfo } from "@/lib/types";
import { DocumentUpload } from "@/components/documents/DocumentUpload";
import { DocumentList } from "@/components/documents/DocumentList";
import { StatsPanel } from "@/components/dashboard/StatsPanel";
import { EvalDashboard } from "@/components/dashboard/EvalDashboard";
import { useState } from "react";

interface Props {
  open: boolean;
  documents: DocumentInfo[];
  selectedDocs: string[];
  onSelectDoc: (id: string) => void;
  onUploadComplete: () => void;
  onDelete: (id: string) => void;
  isUploading: boolean;
}

export function Sidebar({ open, documents, selectedDocs, onSelectDoc, onUploadComplete, onDelete, isUploading }: Props) {
  const [tab, setTab] = useState<"docs" | "stats" | "eval">("docs");

  if (!open) return null;

  return (
    <aside className="w-72 flex-shrink-0 border-r border-border flex flex-col h-full overflow-hidden">
      {/* Tab bar */}
      <div className="flex border-b border-border">
        {(["docs", "stats", "eval"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors
              ${tab === t ? "border-b-2 border-primary text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
            {t === "docs" ? "Documents" : t === "stats" ? "Stats" : "Eval"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "docs" && (
          <div className="p-3 space-y-3">
            <DocumentUpload onUploadComplete={onUploadComplete} />
            {selectedDocs.length > 0 && (
              <p className="text-xs text-primary">
                {selectedDocs.length} doc(s) selected — searches filtered
              </p>
            )}
            <DocumentList
              documents={documents}
              selectedDocs={selectedDocs}
              onSelect={onSelectDoc}
              onDelete={onDelete}
            />
          </div>
        )}
        {tab === "stats" && <StatsPanel />}
        {tab === "eval" && <EvalDashboard />}
      </div>
    </aside>
  );
}
