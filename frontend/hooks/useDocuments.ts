"use client";
import { useState, useCallback, useEffect } from "react";
import { DocumentInfo } from "@/lib/types";
import { listDocuments, uploadDocument, deleteDocument } from "@/lib/api";

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const handleUpload = useCallback(async (file: File) => {
    setIsUploading(true);
    try {
      await uploadDocument(file);
      await fetchDocuments();
    } finally {
      setIsUploading(false);
    }
  }, [fetchDocuments]);

  const handleDelete = useCallback(async (docId: string) => {
    await deleteDocument(docId);
    setDocuments(prev => prev.filter(d => d.doc_id !== docId));
  }, []);

  return {
    documents,
    isLoading,
    isUploading,
    uploadDocument: handleUpload,
    deleteDocument: handleDelete,
    refetch: fetchDocuments
  };
}
