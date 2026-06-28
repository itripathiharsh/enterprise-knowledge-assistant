import axios from "axios";
import { API_BASE_URL } from "./constants";
import { DocumentInfo, StatsData, Source, ChunkResult } from "./types";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("auth_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      if (typeof window !== "undefined") {
        const hadToken = !!localStorage.getItem("auth_token");
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user_id");
        localStorage.removeItem("auth_email");
        if (hadToken) window.location.reload();
      }
    }
    return Promise.reject(err);
  }
);

// ── Documents ─────────────────────────────────────────────────────

export async function uploadDocument(file: File): Promise<{
  doc_id: string;
  doc_name: string;
  total_pages: number;
  total_chunks: number;
  message: string;
}> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function uploadBatch(files: File[]): Promise<any> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const { data } = await api.post("/documents/upload-batch", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const { data } = await api.get(`/documents/?t=${Date.now()}`);
  return data.documents;
}

export async function deleteDocument(docId: string): Promise<void> {
  await api.delete(`/documents/${docId}`);
}

export async function summarizeDocument(docId: string): Promise<string> {
  const { data } = await api.get(`/documents/${docId}/summary`);
  return data.summary;
}

// ── Query ─────────────────────────────────────────────────────────

export async function askQuestion(params: {
  question: string;
  session_id: string;
  doc_filter?: string[];
}): Promise<{
  answer: string;
  sources: Source[];
  chunks: ChunkResult[];
  confidence: number;
  follow_up_questions: string[];
}> {
  const { data } = await api.post("/ask", params);
  return data;
}

export async function submitFeedback(params: {
  session_id: string;
  question: string;
  answer: string;
  feedback: string;
}): Promise<void> {
  await api.post("/feedback", params);
}

export async function getRecentQueries(): Promise<string[]> {
  const { data } = await api.get("/recent-queries");
  return data.queries;
}

// ── Stats ─────────────────────────────────────────────────────────

export async function getStats(): Promise<StatsData> {
  const { data } = await api.get(`/stats/?t=${Date.now()}`);
  return data;
}

export async function getLastEvaluation(): Promise<any> {
  const { data } = await api.get(`/stats/evaluate/last?t=${Date.now()}`);
  return data;
}

export async function getChatHistory(): Promise<
  { role: string; content: string }[]
> {
  const { data } = await api.get(`/query/history?t=${Date.now()}`);
  return data.history;
}
