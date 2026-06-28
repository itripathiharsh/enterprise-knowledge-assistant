"use client";
import { useState, useCallback } from "react";
import { Upload, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { API_BASE_URL } from "@/lib/constants";
import axios from "axios";

interface FileProgress {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  message?: string;
}

interface Props {
  onUploadComplete: () => void;
}

export function DocumentUpload({ onUploadComplete }: Props) {
  const [files, setFiles] = useState<FileProgress[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const validFiles = Array.from(newFiles);
    setFiles(prev => [
      ...prev,
      ...validFiles.map(f => ({ file: f, status: "pending" as const }))
    ]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadAll = async () => {
    if (files.length === 0 || isUploading) return;
    setIsUploading(true);

    // Upload one at a time to show per-file progress
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== "pending") continue;
      
      setFiles(prev => prev.map((f, idx) =>
        idx === i ? { ...f, status: "uploading" } : f
      ));
      
      try {
        const form = new FormData();
        form.append("file", files[i].file);
        const token = localStorage.getItem("auth_token");
        
        const { data } = await axios.post(`${API_BASE_URL}/documents/upload`, form, {
          headers: {
            "Content-Type": "multipart/form-data",
            "Authorization": `Bearer ${token}`
          }
        });
        
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: "done", message: `${data.total_chunks} chunks indexed` } : f
        ));
      } catch (err: any) {
        setFiles(prev => prev.map((f, idx) =>
          idx === i ? { ...f, status: "error", message: err.response?.data?.detail || "Failed" } : f
        ));
      }
    }

    setIsUploading(false);
    onUploadComplete();
    // Clear done files after 3 seconds
    setTimeout(() => setFiles(prev => prev.filter(f => f.status !== "done")), 3000);
  };

  return (
    <div className="space-y-3">
      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input")?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
          ${isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"}`}
      >
        <Upload className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Drop documents here or <span className="text-primary">browse</span>
        </p>
        <p className="text-xs text-muted-foreground/60 mt-1">PDF, MD, TXT, CSV, DOCX, XLSX supported</p>
        <input
          id="file-input"
          type="file"
          accept=".pdf,.md,.txt,.csv,.docx,.xlsx"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
      </div>

      {/* File list with per-file status */}
      {files.length > 0 && (
        <div className="space-y-1.5">
          {files.map((fp, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 text-sm">
              {fp.status === "pending" && <div className="w-4 h-4 rounded-full border-2 border-border flex-shrink-0" />}
              {fp.status === "uploading" && <Loader2 className="w-4 h-4 animate-spin text-primary flex-shrink-0" />}
              {fp.status === "done" && <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />}
              {fp.status === "error" && <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0" />}
              
              <div className="flex-1 min-w-0">
                <p className="truncate font-medium">{fp.file.name}</p>
                {fp.message && (
                  <p className={`text-xs ${fp.status === "error" ? "text-destructive" : "text-muted-foreground"}`}>
                    {fp.message}
                  </p>
                )}
              </div>
              
              {fp.status === "pending" && (
                <button onClick={() => removeFile(i)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))}

          {files.some(f => f.status === "pending") && (
            <button
              onClick={uploadAll}
              disabled={isUploading}
              className="w-full py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium
                         hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isUploading ? "Uploading..." : `Upload ${files.filter(f => f.status === "pending").length} file(s)`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
