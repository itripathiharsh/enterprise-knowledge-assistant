"use client";
import { useEffect, useState } from "react";
import { StatsData } from "@/lib/types";
import { getStats } from "@/lib/api";
import { Database, FileText, Layers, Cpu } from "lucide-react";

export function StatsPanel() {
  const [stats, setStats] = useState<StatsData | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
  }, []);

  if (!stats) return null;

  return (
    <div className="p-3 space-y-3">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Statistics</p>
      <div className="grid grid-cols-2 gap-1.5">
        {[
          { icon: FileText, label: "Documents", value: stats.total_documents },
          { icon: Layers, label: "Pages", value: stats.total_pages },
          { icon: Database, label: "Chunks", value: stats.total_chunks },
          { icon: Cpu, label: "Model", value: "MiniLM" },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="bg-muted/50 rounded-lg p-2 text-center">
            <Icon className="w-3.5 h-3.5 mx-auto mb-0.5 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-sm font-semibold">{value}</p>
          </div>
        ))}
      </div>
      <div className="text-xs text-muted-foreground space-y-0.5">
        <p>Vector DB: {stats.vector_db}</p>
        <p>Embed: {stats.embedding_model}</p>
      </div>
      {stats.recent_queries.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">Recent queries</p>
          {stats.recent_queries.slice(0, 3).map((q, i) => (
            <p key={i} className="text-xs text-muted-foreground truncate py-0.5 border-b border-border last:border-0">{q}</p>
          ))}
        </div>
      )}
    </div>
  );
}
