import { Sparkles } from "lucide-react";
import { protectedJson } from "@/lib/server-protected";

type Insight = { tipo: string; prioridade: string; titulo: string; total: number; acao: string };
type Response = { gerado_em: string; alerts: Insight[] };

export default async function AutomationsPage() {
  const data = await protectedJson<Response>("/api/automation/insights", "Não foi possível gerar os insights.");
  return <div className="mx-auto max-w-6xl"><header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">Automação / inteligência</p><h1 className="mt-1 text-3xl font-bold text-slate-950">Insights operacionais</h1><p className="mt-2 text-slate-500">Alertas automáticos baseados nos dados do CRM. Não dependem de uma IA externa.</p></header>
    {data.alerts.length === 0 ? <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center"><Sparkles className="mx-auto text-emerald-500" /><p className="mt-4 font-semibold">Nenhuma pendência crítica detectada.</p></div> : <div className="grid gap-4 md:grid-cols-2">{data.alerts.map((item, index) => <article key={`${item.tipo}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase text-slate-400">Prioridade {item.prioridade}</p><h2 className="mt-1 text-lg font-bold">{item.titulo}</h2></div><span className="rounded-full bg-emerald-50 px-3 py-1 text-lg font-bold text-emerald-700">{item.total}</span></div><p className="mt-4 text-sm text-slate-600">{item.acao}</p></article>)}</div>}
  </div>;
}
