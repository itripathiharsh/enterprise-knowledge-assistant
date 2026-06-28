"use client";
import { useState, useCallback } from "react";
import axios from "axios";
import { API_BASE_URL } from "@/lib/constants";

interface AuthState {
  token: string | null;
  userId: string | null;
  email: string | null;
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>(() => {
    // Hydrate from localStorage on mount
    if (typeof window === "undefined") return { token: null, userId: null, email: null };
    return {
      token: localStorage.getItem("auth_token"),
      userId: localStorage.getItem("auth_user_id"),
      email: localStorage.getItem("auth_email"),
    };
  });

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await axios.post(`${API_BASE_URL}/auth/login`, { email, password });
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("auth_user_id", data.user_id);
    localStorage.setItem("auth_email", data.email);
    setAuth({ token: data.access_token, userId: data.user_id, email: data.email });
    return data;
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const { data } = await axios.post(`${API_BASE_URL}/auth/register`, { email, password });
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("auth_user_id", data.user_id);
    localStorage.setItem("auth_email", data.email);
    setAuth({ token: data.access_token, userId: data.user_id, email: data.email });
    return data;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user_id");
    localStorage.removeItem("auth_email");
    setAuth({ token: null, userId: null, email: null });
    window.location.reload();
  }, []);

  return { ...auth, isAuthenticated: !!auth.token, login, register, logout };
}
