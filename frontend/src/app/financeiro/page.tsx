import { Banknote, CircleDollarSign, Clock3, RotateCcw } from "lucide-react";
import { protectedJson } from "@/lib/server-protected";

type FinanceSummary = {
  receita_paga: number;
  a_receber: number;
  reembolsado: number;
  cancelado: number;
  saldo_liquido: number;
  quantidades: Record<string, number>;
};

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export default async function FinancePage() {
  const data = await protectedJson<FinanceSummary>("/api/finance/summary", "Não foi possível carregar o financeiro.");
  return <div className="mx-auto max-w-7xl"><header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">Financeiro comercial</p><h1 className="mt-1 text-3xl font-bold text-slate-950">Receita e pagamentos</h1><p className="mt-2 text-slate-500">Visão consolidada do que foi pago, está pendente, foi cancelado ou reembolsado.</p></header>
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric icon={<CircleDollarSign />} title="Receita paga" value={money.format(data.receita_paga)} /><Metric icon={<Clock3 />} title="A receber" value={money.format(data.a_receber)} /><Metric icon={<RotateCcw />} title="Reembolsado" value={money.format(data.reembolsado)} /><Metric icon={<Banknote />} title="Saldo líquido" value={money.format(data.saldo_liquido)} /></section>
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="font-bold text-slate-950">Quantidade por status</h2><div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Object.entries(data.quantidades).map(([status,total]) => <div key={status} className="rounded-xl bg-slate-50 p-4"><p className="text-sm text-slate-500">{status}</p><p className="mt-1 text-2xl font-bold">{total}</p></div>)}</div></section>
  </div>;
}
function Metric({ icon, title, value }: { icon: React.ReactNode; title: string; value: string }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="text-slate-400">{icon}</div><p className="mt-3 text-sm text-slate-500">{title}</p><p className="mt-1 text-2xl font-bold text-slate-950">{value}</p></div>; }
