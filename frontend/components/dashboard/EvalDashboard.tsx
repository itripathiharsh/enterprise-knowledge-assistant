"use client";
import { useState } from "react";
import { Play, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import axios from "axios";
import { API_BASE_URL } from "@/lib/constants";

interface EvalResult {
  id: string;
  question: string;
  expected: string;
  actual: string;
  semantic_similarity: number;
  source_found: boolean;
  confidence: number;
}

interface EvalSummary {
  total_cases: number;
  avg_semantic_similarity: number;
  source_attribution_accuracy: number;
  avg_confidence: number;
}

export function EvalDashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [results, setResults] = useState<EvalResult[]>([]);
  const [error, setError] = useState("");

  const runEval = async () => {
    setIsRunning(true);
    setError("");
    try {
      const token = localStorage.getItem("auth_token");
      const { data } = await axios.post(`${API_BASE_URL}/stats/evaluate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(data.summary);
      setResults(data.results);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Evaluation failed.");
    }
    setIsRunning(false);
  };

  const simColor = (sim: number) =>
    sim >= 0.7 ? "text-green-500" : sim >= 0.4 ? "text-amber-500" : "text-red-500";

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-sm">Evaluation Dashboard</h2>
        <button
          onClick={runEval}
          disabled={isRunning}
          className="flex items-center gap-1.5 text-xs bg-primary text-primary-foreground
                     px-3 py-1.5 rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <Play className="w-3 h-3" />
          {isRunning ? "Running..." : "Run Eval"}
        </button>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      {summary && (
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: "Avg Similarity", value: `${(summary.avg_semantic_similarity * 100).toFixed(1)}%` },
            { label: "Source Accuracy", value: `${(summary.source_attribution_accuracy * 100).toFixed(1)}%` },
            { label: "Avg Confidence", value: `${(summary.avg_confidence * 100).toFixed(1)}%` },
            { label: "Test Cases", value: summary.total_cases }
          ].map(({ label, value }) => (
            <div key={label} className="bg-muted/50 rounded-lg p-2.5 text-center">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {results.map((r) => (
            <div key={r.id} className="border border-border rounded-lg p-2.5 text-xs space-y-1">
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium">{r.question}</p>
                {r.source_found
                  ? <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                  : <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />}
              </div>
              <p className={`font-mono ${simColor(r.semantic_similarity)}`}>
                Similarity: {(r.semantic_similarity * 100).toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
