import { protectedJson } from "@/lib/server-protected";

type ConversionItem = { leads: number; vendidos: number; conversao: number };
type CustomerAnalytics = {
  por_faixa_etaria: (ConversionItem & { faixa: string })[];
  por_genero: (ConversionItem & { genero: string })[];
  por_cidade: (ConversionItem & { cidade: string })[];
  por_orcamento: (ConversionItem & { faixa: string })[];
  por_objetivo: (ConversionItem & { objetivo: string })[];
  receita_por_orcamento: { faixa: string; receita: number }[];
  receita_por_objetivo: { objetivo: string; receita: number }[];
  por_tipo_cliente: (ConversionItem & { tipo: string })[];
  por_segmento: (ConversionItem & { segmento: string })[];
  por_oferta: (ConversionItem & { oferta: string })[];
  por_formato: (ConversionItem & { formato: string })[];
  por_tamanho_equipe: (ConversionItem & { faixa: string })[];
};

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export default async function CustomerAnalyticsPage() {
  const analytics = await protectedJson<CustomerAnalytics>("/api/customer-analytics", "Não foi possível carregar o Customer Analytics.");

  return <div className="mx-auto max-w-7xl">
    <header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">Inteligência de clientes</p><h1 className="mt-1 text-3xl font-bold text-slate-950">Customer Analytics</h1><p className="mt-2 text-slate-500">B2B/B2C, segmento, equipe, oferta, formato e perfil de conversão.</p></header>

    <section className="grid gap-6 lg:grid-cols-2">
      <AnalyticsCard title="Tipo de cliente" items={analytics.por_tipo_cliente.map((x) => ({ label: x.tipo, ...x }))} />
      <AnalyticsCard title="Tamanho da equipe" items={analytics.por_tamanho_equipe.map((x) => ({ label: x.faixa, ...x }))} />
      <AnalyticsCard title="Segmento" items={analytics.por_segmento.map((x) => ({ label: x.segmento, ...x }))} />
      <AnalyticsCard title="Oferta de interesse" items={analytics.por_oferta.map((x) => ({ label: x.oferta, ...x }))} />
      <AnalyticsCard title="Formato" items={analytics.por_formato.map((x) => ({ label: x.formato, ...x }))} />
      <AnalyticsCard title="Cidade" items={analytics.por_cidade.map((x) => ({ label: x.cidade, ...x }))} />
      <AnalyticsCard title="Faixa de orçamento" items={analytics.por_orcamento.map((x) => ({ label: x.faixa, ...x }))} />
      <AnalyticsCard title="Faixa etária (B2C)" items={analytics.por_faixa_etaria.map((x) => ({ label: x.faixa, ...x }))} />
      <AnalyticsCard title="Gênero (B2C)" items={analytics.por_genero.map((x) => ({ label: x.genero, ...x }))} />
    </section>

    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-bold text-slate-950">Objetivo do cliente</h2><p className="mt-1 text-sm text-slate-500">Por que os clientes demonstraram interesse.</p><div className="mt-6 overflow-x-auto"><table className="w-full min-w-[700px] text-left text-sm"><thead className="border-b border-slate-200 text-xs uppercase text-slate-400"><tr><th className="py-3">Objetivo</th><th className="py-3">Leads</th><th className="py-3">Fechados</th><th className="py-3">Conversão</th></tr></thead><tbody className="divide-y divide-slate-100">{analytics.por_objetivo.map((item) => <tr key={item.objetivo}><td className="py-4 font-semibold">{item.objetivo}</td><td className="py-4">{item.leads}</td><td className="py-4">{item.vendidos}</td><td className="py-4 font-bold text-emerald-600">{item.conversao.toFixed(2)}%</td></tr>)}</tbody></table></div></section>

    <section className="mt-6 grid gap-6 lg:grid-cols-2"><RevenueCard title="Receita por orçamento" items={analytics.receita_por_orcamento.map((x) => ({ label: x.faixa, value: x.receita }))} /><RevenueCard title="Receita por objetivo" items={analytics.receita_por_objetivo.map((x) => ({ label: x.objetivo, value: x.receita }))} /></section>
  </div>;
}

function AnalyticsCard({ title, items }: { title: string; items: { label: string; leads: number; vendidos: number; conversao: number }[] }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-bold text-slate-950">{title}</h2><div className="mt-6 space-y-4">{items.length === 0 ? <p className="text-sm text-slate-500">Sem dados suficientes.</p> : items.map((item) => <div key={item.label} className="rounded-xl bg-slate-50 p-4"><div className="flex items-center justify-between gap-4"><strong className="text-slate-900">{item.label}</strong><strong className="text-emerald-600">{item.conversao.toFixed(2)}%</strong></div><p className="mt-2 text-xs text-slate-500">{item.leads} Lead(s) · {item.vendidos} fechado(s)</p><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(item.conversao, 100)}%` }} /></div></div>)}</div></div>;
}

function RevenueCard({ title, items }: { title: string; items: { label: string; value: number }[] }) {
  const max = Math.max(1, ...items.map((item) => item.value));
  return <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-bold text-slate-950">{title}</h2><div className="mt-6 space-y-5">{items.length === 0 ? <p className="text-sm text-slate-500">Ainda não há receita suficiente para análise.</p> : items.map((item) => <div key={item.label}><div className="mb-2 flex justify-between gap-4"><span className="text-sm font-medium">{item.label}</span><strong>{money.format(item.value)}</strong></div><div className="h-3 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-blue-500" style={{ width: `${(item.value / max) * 100}%` }} /></div></div>)}</div></div>;
}
