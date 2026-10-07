"use client";

import Link from "next/link";
import { useState } from "react";

import { clientApi } from "@/lib/client-api";

type Lead = {
  id: number;
  nome: string;
  origem: string;
  objetivo: string;
  status: string;
  interesse: string;
  contatos: number;
};

type Props = { initialLeads: Lead[] };

const stages = [
  "Lead",
  "Contato realizado",
  "Interessado",
  "Reunião",
  "Proposta",
  "Negociação",
  "Fechado",
  "Pós-venda",
  "Perdido",
];

export default function KanbanBoard({ initialLeads }: Props) {
  const [leads, setLeads] = useState(initialLeads);
  const [draggingId, setDraggingId] = useState<number | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  async function changeStatus(leadId: number, newStatus: string) {
    const currentLead = leads.find((lead) => lead.id === leadId);
    if (!currentLead || currentLead.status === newStatus) return;

    const oldStatus = currentLead.status;
    setSavingId(leadId);
    setLeads((current) => current.map((lead) => lead.id === leadId ? { ...lead, status: newStatus } : lead));

    const response = await clientApi(`/api/leads/${leadId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });

    if (!response.ok) {
      setLeads((current) => current.map((lead) => lead.id === leadId ? { ...lead, status: oldStatus } : lead));
      alert("Não foi possível atualizar o status.");
    }

    setSavingId(null);
  }

  return (
    <div className="overflow-x-auto pb-4">
      <div className="flex min-w-max gap-4">
        {stages.map((stage) => {
          const stageLeads = leads.filter((lead) => lead.status === stage);
          return (
            <section key={stage} onDragOver={(event) => event.preventDefault()} onDrop={() => { if (draggingId !== null) changeStatus(draggingId, stage); setDraggingId(null); }} className="w-80 shrink-0 rounded-2xl border border-slate-200 bg-slate-100 p-4">
              <div className="mb-4 flex items-center justify-between"><h2 className="font-bold text-slate-900">{stage}</h2><span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-slate-600 shadow-sm">{stageLeads.length}</span></div>
              <div className="min-h-32 space-y-3">
                {stageLeads.map((lead) => (
                  <article key={lead.id} draggable onDragStart={() => setDraggingId(lead.id)} onDragEnd={() => setDraggingId(null)} className={["cursor-grab rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition", savingId === lead.id ? "opacity-50" : "hover:-translate-y-0.5 hover:shadow-md"].join(" ")}>
                    <Link href={`/leads/${lead.id}`} className="font-bold text-slate-950 hover:text-emerald-600">{lead.nome}</Link>
                    <p className="mt-2 text-xs font-medium uppercase tracking-wide text-slate-400">{lead.origem}</p>
                    <p className="mt-3 text-sm text-slate-600">{lead.objetivo}</p>
                    <div className="mt-4 flex items-center justify-between"><span className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">{lead.interesse}</span><span className="text-xs text-slate-400">{lead.contatos} contatos</span></div>
                    {savingId === lead.id && <p className="mt-3 text-xs font-medium text-slate-400">Salvando...</p>}
                  </article>
                ))}
                {stageLeads.length === 0 && <div className="rounded-xl border border-dashed border-slate-300 p-5 text-center text-xs text-slate-400">Arraste um Lead para cá</div>}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
