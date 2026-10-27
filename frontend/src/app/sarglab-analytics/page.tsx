import Link from "next/link";
import { protectedJson } from "@/lib/server-protected";

type GroupItem = { solicitacoes: number; leads_unicos: number };
type Source = GroupItem & { origem: string };
type Campaign = GroupItem & { campanha: string };
type Row = {
  lead_id: number;
  nome: string;
  email: string | null;
  area_profissional: string | null;
  status_crm: string;
  produto: "instagram" | "primeiro";
  origem: string;
  campanha: string;
  data: string;
};
type Analytics = {
  produto: string;
  dias: number;
  atualizado_em: string;
  resumo: {
    solicitacoes: number;
    leads_unicos: number;
    solicitacoes_adicionais: number;
    leads_convertidos_crm: number;
  };
  emails: {
    total_registros: number;
    envios_smtp: number;
    falhas: number;
    ignorados: number;
  };
  por_origem: Source[];
  por_campanha: Campaign[];
  por_dia: { data: string; solicitacoes: number }[];
  por_status_crm: { status: string; leads_unicos: number }[];
  recentes: Row[];
  observacao: string;
};

const produtos = [
  { id: "instagram", nome: "Instagram sob análise" },
  { id: "primeiro", nome: "IA para quem tem trabalho pra fazer" },
  { id: "todos", nome: "Todos os e-books" },
] as const;
const periodos = [
  { id: 7, nome: "7 dias" },
  { id: 30, nome: "30 dias" },
  { id: 90, nome: "90 dias" },
  { id: 365, nome: "365 dias" },
  { id: 0, nome: "Todo o histórico" },
] as const;
const formatter = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" });
const dateTime = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
const localDate = (iso: string) => {
  const [year, month, day] = iso.slice(0, 10).split("-").map(Number);
  return formatter.format(new Date(year, month - 1, day));
};
const href = (produto: string, dias: number) => `/sarglab-analytics?produto=${produto}&dias=${dias}`;

export default async function SarglabAnalyticsPage({
  searchParams,
}: {
  searchParams: Promise<{ produto?: string; dias?: string }>;
}) {
  const params = await searchParams;
  const produto = produtos.find((p) => p.id === params.produto)?.id ?? "instagram";
  const dias = periodos.find((p) => String(p.id) === params.dias)?.id ?? 30;
  const data = await protectedJson<Analytics>(
    `/api/sarglab/ebooks/analytics?produto=${produto}&dias=${dias}`,
    "Não foi possível carregar a captação de leads da SargLab."
  );
  const maxDia = Math.max(1, ...data.por_dia.map((item) => item.solicitacoes));

  return (
    <main className="mx-auto max-w-7xl space-y-7">
      <header>
        <p className="text-sm font-semibold uppercase tracking-wide text-cobalt-600">SargLab · Inteligência de captação</p>
        <h1 className="mt-1 text-3xl font-bold text-midnight">Leads dos e-books</h1>
        <p className="mt-2 text-slate-500">Acompanhe solicitações de materiais, origens de campanha e registros de e-mail enviados pelo CRM.</p>
      </header>

      <section className="space-y-3" aria-label="Filtros">
        <div className="flex flex-wrap gap-2">
          {produtos.map((p) => <Link key={p.id} href={href(p.id, dias)}
            aria-current={produto === p.id ? "page" : undefined}
            className={`rounded-xl border px-4 py-2 text-sm font-semibold ${produto === p.id ? "border-cobalt-500 bg-cobalt-500 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-cobalt-400"}`}>
            {p.nome}
          </Link>)}
        </div>
        <div className="flex flex-wrap gap-2">
          {periodos.map((p) => <Link key={p.id} href={href(produto, p.id)}
            aria-current={dias === p.id ? "page" : undefined}
            className={`rounded-lg border px-3 py-1.5 text-xs font-medium ${dias === p.id ? "border-slate-800 bg-slate-800 text-white" : "border-slate-200 bg-white text-slate-500 hover:border-slate-500"}`}>
            {p.nome}
          </Link>)}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="Solicitações" value={data.resumo.solicitacoes} info="Envios de formulário, não downloads" />
        <Metric title="Leads únicos" value={data.resumo.leads_unicos} info="Contatos distintos no período" />
        <Metric title="Solicitações adicionais" value={data.resumo.solicitacoes_adicionais} info="Pedidos além do primeiro por contato" />
        <Metric title="Leads fechados no CRM" value={data.resumo.leads_convertidos_crm} info="Status comercial, não venda atribuída" />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric title="E-mails aceitos pelo SMTP" value={data.emails.envios_smtp} info="Aceite do provedor; não comprova recebimento" />
        <Metric title="Falhas registradas" value={data.emails.falhas} info="Tentativas com falha" />
        <Metric title="Envios ignorados" value={data.emails.ignorados} info="Rotina não executada" />
        <Metric title="Logs de e-mail" value={data.emails.total_registros} info="Registros associados ao material no período" />
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-midnight">Solicitações por dia</h2>
          <p className="mt-1 text-sm text-slate-500">Evolução dos formulários registrados no período escolhido.</p>
          <div className="mt-6 max-h-[320px] space-y-3 overflow-y-auto">
            {data.por_dia.length === 0 ? <Empty /> : data.por_dia.map((row) => <div key={row.data} className="flex items-center gap-3 text-sm">
              <span className="w-12 shrink-0 text-slate-500">{localDate(row.data)}</span>
              <div className="h-3 flex-1 rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-cobalt-500" style={{ width: `${100 * row.solicitacoes / maxDia}%` }} />
              </div>
              <strong className="w-9 text-right">{row.solicitacoes}</strong>
            </div>)}
          </div>
        </div>
        <div className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-bold text-midnight">Origem da captação</h2>
          <p className="mt-1 text-sm text-slate-500">UTM de origem; na ausência dela, a origem estimada do formulário.</p>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-left text-sm"><thead><tr className="border-b text-xs uppercase text-slate-500">
              <th className="pb-3">Origem</th><th className="pb-3 text-right">Pedidos</th><th className="pb-3 text-right">Leads</th>
            </tr></thead><tbody className="divide-y divide-slate-100">
              {data.por_origem.map((row) => <tr key={row.origem}><td className="py-3 font-medium">{row.origem}</td><td className="py-3 text-right">{row.solicitacoes}</td><td className="py-3 text-right">{row.leads_unicos}</td></tr>)}
            </tbody></table>
            {data.por_origem.length === 0 && <Empty />}
          </div>
        </div>
      </section>

      <section className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-midnight">Campanhas UTM</h2>
        <p className="mt-1 text-sm text-slate-500">Atribuição por campanha informada no link, não prova de venda.</p>
        <div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead>
          <tr className="border-b text-xs uppercase text-slate-500"><th className="pb-3">Campanha</th><th className="pb-3 text-right">Pedidos</th><th className="pb-3 text-right">Leads únicos</th></tr>
        </thead><tbody className="divide-y divide-slate-100">{data.por_campanha.map((row) => <tr key={row.campanha}>
          <td className="py-3 font-medium">{row.campanha}</td><td className="py-3 text-right">{row.solicitacoes}</td><td className="py-3 text-right">{row.leads_unicos}</td>
        </tr>)}</tbody></table>{data.por_campanha.length === 0 && <Empty />}</div>
      </section>

      <section className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-midnight">Solicitações recentes</h2>
        <p className="mt-1 text-sm text-slate-500">Últimos 50 envios de formulário. A mesma pessoa pode aparecer mais de uma vez.</p>
        <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[800px] text-left text-sm">
          <thead><tr className="border-b text-xs uppercase text-slate-500">
            <th className="py-3">Contato</th><th className="py-3">Data</th><th className="py-3">Material</th>
            <th className="py-3">Origem</th><th className="py-3">Status CRM</th>
          </tr></thead>
          <tbody className="divide-y divide-slate-100">{data.recentes.map((item, i) => <tr key={`${item.lead_id}-${i}`}>
            <td className="py-3"><Link className="font-semibold text-cobalt-600 hover:underline" href={`/leads/${item.lead_id}`}>{item.nome}</Link>
              <div className="text-xs text-slate-500">{item.email ?? "Sem e-mail"}</div></td>
            <td className="py-3">{dateTime.format(new Date(item.data))}</td>
            <td className="py-3">{item.produto === "instagram" ? "Instagram sob análise" : "IA no dia a dia"}</td>
            <td className="py-3">{item.origem}</td><td className="py-3">{item.status_crm}</td>
          </tr>)}</tbody>
        </table>{data.recentes.length === 0 && <Empty />}</div>
      </section>
      <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-950">{data.observacao}</p>
    </main>
  );
}

function Metric({ title, value, info }: { title: string; value: number; info: string }) {
  return <div className="rounded-card border border-slate-200 bg-white p-5 shadow-sm">
    <p className="text-sm font-medium text-slate-600">{title}</p>
    <p className="mt-2 text-3xl font-bold text-midnight">{value.toLocaleString("pt-BR")}</p>
    <p className="mt-1 text-xs text-slate-500">{info}</p>
  </div>;
}
function Empty() { return <p className="py-6 text-sm text-slate-500">Nenhum registro neste filtro.</p>; }
