import { Source } from "@/lib/types";
import { FileText } from "lucide-react";

interface Props { source: Source }

export function SourceCard({ source }: Props) {
  return (
    <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-border bg-muted/30 text-xs">
      <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
      <span className="text-muted-foreground truncate max-w-[150px]">{source.document}</span>
      <span className="text-muted-foreground/60 flex-shrink-0">p.{source.page}</span>
    </div>
  );
}
