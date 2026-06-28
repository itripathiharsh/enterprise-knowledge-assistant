export interface Source {
  document: string;
  doc_id: string;
  page: number;
}

export interface ChunkResult {
  text: string;
  doc_name: string;
  page_number: number;
  chunk_index: number;
  similarity_score: number;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  chunks?: ChunkResult[];
  confidence?: number;
  followUpQuestions?: string[];
  isStreaming?: boolean;
  timestamp: Date;
}

export interface DocumentInfo {
  doc_id: string;
  doc_name: string;
  total_pages: number;
  total_chunks: number;
  uploaded_at: string;
  file_size_kb: number;
}

export interface StatsData {
  total_documents: number;
  total_pages: number;
  total_chunks: number;
  embedding_model: string;
  vector_db: string;
  recent_queries: string[];
}

export type ThinkingStep =
  | "understanding"
  | "planning"
  | "searching"
  | "reading"
  | "gathering"
  | "synthesizing"
  | "validating"
  | "generating"
  | "done";
