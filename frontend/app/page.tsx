"use client";
import { useState } from "react";
import { useChat } from "@/hooks/useChat";
import { useDocuments } from "@/hooks/useDocuments";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { ChatInput } from "@/components/chat/ChatInput";
import { useAuth } from "@/hooks/useAuth";
import { LoginModal } from "@/components/auth/LoginModal";

export default function Home() {
  const { messages, isLoading, thinkingStep, sendMessage, clearChat, sessionId } = useChat();
  const { documents, uploadDocument, deleteDocument, isUploading, refetch } = useDocuments();
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const { isAuthenticated } = useAuth();
  const [authReady, setAuthReady] = useState(false);

  // Show login modal if not authenticated
  if (!authReady && !isAuthenticated) {
    return <LoginModal onSuccess={() => {
      setAuthReady(true);
      refetch();
    }} />;
  }

  const handleSend = (question: string) => {
    sendMessage(question, selectedDocs.length > 0 ? selectedDocs : undefined);
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar
        open={sidebarOpen}
        documents={documents}
        selectedDocs={selectedDocs}
        onSelectDoc={(id) => setSelectedDocs(prev =>
          prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
        )}
        onUploadComplete={refetch}
        onDelete={deleteDocument}
        isUploading={isUploading}
      />

      <main className="flex flex-col flex-1 min-w-0">
        <Header
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onClearChat={clearChat}
        />

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center max-w-md px-4">
                <h2 className="text-2xl font-semibold mb-2">Enterprise Knowledge Assistant</h2>
                <p className="text-muted-foreground text-sm">
                  Upload internal documents and ask questions in natural language.
                  I&apos;ll find the answers and cite my sources.
                </p>
              </div>
            </div>
          ) : (
            <ChatWindow
              messages={messages}
              thinkingStep={thinkingStep}
              onFollowUp={handleSend}
              sessionId={sessionId}
            />
          )}
        </div>

        <div className="border-t border-border p-4">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
            disabled={documents.length === 0}
            placeholder={documents.length === 0
              ? "Upload documents to start asking questions..."
              : "Ask a question about your documents..."}
          />
          {selectedDocs.length > 0 && (
            <p className="text-xs text-muted-foreground mt-1.5 text-center">
              Searching in {selectedDocs.length} selected document(s)
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
