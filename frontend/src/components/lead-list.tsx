"use client";

import Link from "next/link";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

type Lead = {
  id: number;
  nome: string;
  origem: string;
  objetivo: string;
  status: string;
  interesse: string;
  contatos: number;
  tipo_cliente: string;
  empresa: string | null;
  email: string | null;
  oferta_interesse: string | null;
};

export default function LeadList({ leads }: { leads: Lead[] }) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return leads;
    return leads.filter((lead) => [lead.nome, lead.empresa, lead.email, lead.origem, lead.status, lead.oferta_interesse].some((value) => value?.toLowerCase().includes(q)));
  }, [leads, query]);

  return <>
    <div className="mb-5 flex max-w-xl items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <Search size={18} className="text-slate-400" />
      <input value={query} onChange={(e) => setQuery(e.target.value)} type="search" placeholder="Buscar por nome, empresa, e-mail, origem ou etapa..." className="w-full bg-transparent text-sm outline-none" />
    </div>

    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1050px] text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr><th className="px-5 py-4">Contato</th><th className="px-5 py-4">Empresa / tipo</th><th className="px-5 py-4">Origem</th><th className="px-5 py-4">Oferta</th><th className="px-5 py-4">Etapa</th><th className="px-5 py-4">Interesse</th><th className="px-5 py-4 text-right">Contatos</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((lead) => <tr key={lead.id} className="hover:bg-slate-50">
              <td className="px-5 py-4"><Link href={`/leads/${lead.id}`} className="font-semibold text-slate-900 hover:text-emerald-600">{lead.nome}</Link><p className="mt-1 text-xs text-slate-400">{lead.email ?? lead.objetivo}</p></td>
              <td className="px-5 py-4"><p className="font-medium text-slate-700">{lead.empresa ?? "—"}</p><p className="text-xs text-slate-400">{lead.tipo_cliente}</p></td>
              <td className="px-5 py-4 text-slate-600">{lead.origem}</td>
              <td className="px-5 py-4 text-slate-600">{lead.oferta_interesse ?? "—"}</td>
              <td className="px-5 py-4"><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">{lead.status}</span></td>
              <td className="px-5 py-4"><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{lead.interesse}</span></td>
              <td className="px-5 py-4 text-right font-semibold">{lead.contatos}</td>
            </tr>)}
            {filtered.length === 0 && <tr><td colSpan={7} className="px-5 py-10 text-center text-slate-500">Nenhum Lead encontrado.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  </>;
}
