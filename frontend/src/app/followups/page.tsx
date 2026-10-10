import { protectedJson } from "@/lib/server-protected";
import Link from "next/link";
import { CalendarClock, MessageCircle, Target } from "lucide-react";

type FollowUp = {
  id: string;
  source: "interacao" | "proxima_acao";
  interaction_id: number | null;
  lead_id: number;
  lead_nome: string;
  empresa: string | null;
  tipo: string;
  descricao: string;
  resultado: string | null;
  follow_up_em: string;
};

// O instante de referência é capturado junto com os dados (fora do render do
// componente), para o render ser puro e "vencida" usar um único "agora".
async function getFollowUps(): Promise<{ followups: FollowUp[]; now: number }> {
  const followups = await protectedJson<FollowUp[]>("/api/followups", "Não foi possível carregar os follow-ups.");
  return { followups, now: Date.now() };
}

export default async function FollowUpsPage() {
  const { followups, now } = await getFollowUps();
  const overdue = followups.filter((item) => new Date(item.follow_up_em).getTime() < now).length;

  return <div className="mx-auto max-w-6xl">
    <header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">Comercial</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Follow-ups e próximas ações</h1><p className="mt-2 text-slate-500">Agenda única de retornos registrados nas interações e próximas ações da ficha comercial.</p></header>

    <section className="mb-6 grid gap-4 sm:grid-cols-2"><div className="rounded-2xl bg-slate-950 p-6 text-white"><div className="flex items-center gap-3"><CalendarClock className="text-emerald-400" /><div><p className="text-sm text-slate-400">Ações agendadas</p><p className="text-3xl font-bold">{followups.length}</p></div></div></div><div className="rounded-2xl border border-amber-200 bg-amber-50 p-6"><p className="text-sm text-amber-700">Vencidas</p><p className="mt-1 text-3xl font-bold text-amber-950">{overdue}</p></div></section>

    {followups.length === 0 ? <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-500 shadow-sm">Nenhum follow-up ou próxima ação agendada.</div> : <div className="space-y-4">{followups.map((followup) => {
      const isOverdue = new Date(followup.follow_up_em).getTime() < now;
      return <div key={followup.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-col justify-between gap-5 md:flex-row md:items-center"><div><div className="flex flex-wrap items-center gap-2"><Link href={`/leads/${followup.lead_id}`} className="text-lg font-bold text-slate-950 transition hover:text-emerald-600">{followup.lead_nome}</Link><span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{followup.source === "proxima_acao" ? "Ficha CRM" : "Interação"}</span></div>{followup.empresa && <p className="mt-1 text-xs text-slate-400">{followup.empresa}</p>}<div className="mt-2 flex items-center gap-2 text-sm text-slate-500">{followup.source === "proxima_acao" ? <Target size={16} /> : <MessageCircle size={16} />}{followup.tipo}</div><p className="mt-3 text-sm text-slate-600">{followup.descricao}</p>{followup.resultado && <span className="mt-3 inline-block rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">{followup.resultado}</span>}</div><div className={isOverdue ? "rounded-xl bg-red-50 px-5 py-4" : "rounded-xl bg-amber-50 px-5 py-4"}><p className={isOverdue ? "text-xs font-semibold uppercase text-red-700" : "text-xs font-semibold uppercase text-amber-700"}>{isOverdue ? "Ação vencida" : "Agendado para"}</p><p className={isOverdue ? "mt-1 font-bold text-red-950" : "mt-1 font-bold text-amber-950"}>{new Date(followup.follow_up_em).toLocaleString("pt-BR")}</p></div></div></div>;
    })}</div>}
  </div>;
}
