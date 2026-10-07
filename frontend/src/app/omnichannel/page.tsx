import Link from "next/link";
import { MessagesSquare } from "lucide-react";
import { protectedJson } from "@/lib/server-protected";

type Summary = { por_canal: { canal: string; total: number }[]; recentes: { interaction_id: number; lead_id: number; lead_nome: string; tipo: string; resultado: string | null; criado_em: string }[] };

export default async function OmnichannelPage() {
  const data = await protectedJson<Summary>("/api/omnichannel/summary", "Não foi possível carregar o Omnichannel.");
  return <div className="mx-auto max-w-7xl"><header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">Omnichannel</p><h1 className="mt-1 text-3xl font-bold text-slate-950">Canais de relacionamento</h1><p className="mt-2 text-slate-500">MVP multicanal baseado nas interações registradas no CRM.</p></header>
    <section className="grid gap-4 md:grid-cols-3">{data.por_canal.map((item) => <div key={item.canal} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><MessagesSquare className="text-slate-400" /><p className="mt-3 font-semibold text-slate-700">{item.canal}</p><p className="mt-1 text-3xl font-bold">{item.total}</p></div>)}</section>
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="font-bold text-slate-950">Interações recentes</h2><div className="mt-5 divide-y divide-slate-100">{data.recentes.map((item) => <div key={item.interaction_id} className="flex items-center justify-between gap-4 py-4"><div><Link href={`/leads/${item.lead_id}`} className="font-semibold hover:text-emerald-600">{item.lead_nome}</Link><p className="text-sm text-slate-500">{item.tipo}{item.resultado ? ` · ${item.resultado}` : ""}</p></div><span className="text-xs text-slate-400">{new Date(item.criado_em).toLocaleString("pt-BR")}</span></div>)}</div></section>
  </div>;
}
