"use client";

import { useEffect, useState } from "react";
import { Bot, ShieldCheck } from "lucide-react";
import { clientApi } from "@/lib/client-api";

type AgentStatus = { agent: string; status: string; mode: string; integrations: { whatsapp: boolean; llm: boolean; database: boolean } };

export default function AssistenteSaraPage() {
  const [data, setData] = useState<AgentStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    clientApi("/api/agent/status", { signal: controller.signal })
      .then(async (r) => { if (!r.ok) throw new Error(`Falha ao consultar Sara (HTTP ${r.status})`); return r.json() as Promise<AgentStatus>; })
      .then(setData)
      .catch((e: unknown) => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : "Não foi possível consultar o agente"); });
    return () => controller.abort();
  }, []);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <header className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm">
        <div className="flex items-center gap-3"><Bot size={32} className="text-cobalt-600" />
          <div><p className="text-sm font-semibold text-cobalt-600">SARGTECH / Inteligência Comercial</p>
          <h1 className="text-3xl font-bold text-midnight">Assistente Sara</h1></div></div>
        <p className="mt-4 text-slate-600">Painel inicial de integração ao Gestão Inteligente. As conversas e a IA ainda não estão ativas.</p>
      </header>
      <section className="rounded-2xl border border-slate-200 bg-white p-6">
        <div className="flex items-center gap-2"><ShieldCheck className="text-cobalt-600" /><h2 className="text-lg font-bold">Conexão com o CRM</h2></div>
        {error ? <p role="alert" className="mt-4 text-red-700">{error}</p> :
          !data ? <p className="mt-4 text-slate-500">Verificando o módulo...</p> :
          <div className="mt-4 space-y-2 text-sm text-slate-700">
            <p>Agente: <strong>{data.agent}</strong></p><p>Status: <strong>{data.status}</strong></p>
            <p>Modo: <strong>{data.mode}</strong></p>
            <p>WhatsApp: {data.integrations.whatsapp ? "configurado" : "não conectado"}</p>
            <p>IA generativa: {data.integrations.llm ? "configurada" : "não conectada"}</p>
            <p>Persistência de conversas: {data.integrations.database ? "configurada" : "pendente"}</p>
          </div>}
      </section>
    </div>
  );
}
