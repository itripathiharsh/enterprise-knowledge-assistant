import { DocumentInfo } from "@/lib/types";
import { DocumentCard } from "./DocumentCard";

interface Props {
  documents: DocumentInfo[];
  selectedDocs: string[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function DocumentList({ documents, selectedDocs, onSelect, onDelete }: Props) {
  if (documents.length === 0) {
    return <p className="text-xs text-muted-foreground text-center py-4">No documents yet. Upload a PDF to get started.</p>;
  }
  return (
    <div className="flex flex-col gap-1.5">
      {documents.map((doc) => (
        <DocumentCard key={doc.doc_id} doc={doc}
          isSelected={selectedDocs.includes(doc.doc_id)}
          onSelect={() => onSelect(doc.doc_id)}
          onDelete={() => onDelete(doc.doc_id)} />
      ))}
    </div>
  );
}
