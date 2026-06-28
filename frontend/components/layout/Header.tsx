"use client";
import { Menu, Moon, Sun, Trash2, LogOut } from "lucide-react";
import { useTheme } from "next-themes";
import { useAuth } from "@/hooks/useAuth";

interface Props {
  onToggleSidebar: () => void;
  onClearChat: () => void;
}

export function Header({ onToggleSidebar, onClearChat }: Props) {
  const { theme, setTheme } = useTheme();
  const { email, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-border">
      <div className="flex items-center gap-3">
        <button onClick={onToggleSidebar} className="p-1.5 rounded-lg hover:bg-muted transition-colors">
          <Menu className="w-4 h-4" />
        </button>
        <h1 className="text-sm font-semibold">Knowledge Assistant</h1>
      </div>
      <div className="flex items-center gap-2">
        {email && <span className="text-xs text-muted-foreground hidden sm:block">{email}</span>}
        <button onClick={onClearChat} title="Clear chat"
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
          <Trash2 className="w-4 h-4" />
        </button>
        <button onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
          {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <button onClick={logout} title="Sign out"
          className="p-1.5 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
