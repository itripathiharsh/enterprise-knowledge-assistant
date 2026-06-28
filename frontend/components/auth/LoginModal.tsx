"use client";
import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";

interface Props { onSuccess: () => void; }

export function LoginModal({ onSuccess }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async () => {
    if (!email || password.length < 8) {
      setError("Enter a valid email and password (min 8 chars).");
      return;
    }
    setLoading(true);
    setError("");
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
      onSuccess();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Something went wrong.");
    }
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-card border border-border rounded-2xl p-8 w-full max-w-sm shadow-xl">
        <h1 className="text-xl font-semibold mb-1">Knowledge Assistant</h1>
        <p className="text-sm text-muted-foreground mb-6">
          {mode === "login" ? "Sign in to continue." : "Create your account."}
        </p>

        <div className="flex gap-2 mb-4">
          {(["login", "register"] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)}
              className={`flex-1 py-1.5 rounded-lg text-sm transition-colors
                ${mode === m ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:text-foreground"}`}>
              {m === "login" ? "Sign In" : "Register"}
            </button>
          ))}
        </div>

        <div className="space-y-3">
          <input type="email" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm outline-none focus:ring-2 focus:ring-primary/30" />
          <input type="password" placeholder="Password (min 8 chars)" value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            className="w-full px-3 py-2 rounded-lg border border-border bg-background text-sm outline-none focus:ring-2 focus:ring-primary/30" />
        </div>

        {error && <p className="text-xs text-red-500 mt-2">{error}</p>}

        <button onClick={handleSubmit} disabled={loading}
          className="w-full mt-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium
                     hover:bg-primary/90 disabled:opacity-50 transition-colors">
          {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>
      </div>
    </div>
  );
}
