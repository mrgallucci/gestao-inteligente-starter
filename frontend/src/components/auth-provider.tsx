"use client";

import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { AuthUser } from "@/lib/auth";

type AuthContextType = {
  user: AuthUser | null;
  loading: boolean;
  login: (user: AuthUser) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

// Busca o usuário da sessão sem tocar em estado React (permite usar no effect
// via .then, sem setState síncrono dentro do effect).
async function fetchSessionUser(): Promise<AuthUser | null> {
  try {
    const response = await fetch("/api/session/me", { cache: "no-store" });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return {
      id: data.id,
      nome: data.nome,
      email: data.email,
      role: data.role,
      lead_id: data.lead_id ?? null,
      ativo: data.ativo ?? true,
    };
  } catch {
    return null;
  }
}

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshUser() {
    const sessionUser = await fetchSessionUser();
    setUser(sessionUser);
    setLoading(false);
  }

  useEffect(() => {
    let active = true;

    fetchSessionUser().then((sessionUser) => {
      if (!active) return;
      setUser(sessionUser);
      setLoading(false);
    });

    return () => {
      active = false;
    };
  }, []);

  function login(authenticatedUser: AuthUser) {
    setUser(authenticatedUser);
  }

  function logout() {
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth precisa estar dentro de AuthProvider");
  return context;
}
