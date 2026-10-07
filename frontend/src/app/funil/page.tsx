import { protectedJson } from "@/lib/server-protected";
import KanbanBoard from "@/components/kanban-board";

type Lead = {
  id: number;
  nome: string;
  origem: string;
  objetivo: string;
  status: string;
  interesse: string;
  contatos: number;
};

async function getLeads(): Promise<Lead[]> {
  return protectedJson<Lead[]>("/api/leads", "Não foi possível carregar o funil.");
}

export default async function FunilPage() {
  const leads = await getLeads();

  const vendidos = leads.filter(
    (lead) => ["Fechado", "Pós-venda"].includes(lead.status)
  ).length;

  const perdidos = leads.filter(
    (lead) => lead.status === "Perdido"
  ).length;

  const ativos =
    leads.length - vendidos - perdidos;

  return (
    <div className="mx-auto max-w-[1800px]">
      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Comercial
        </p>

        <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
          Funil de vendas
        </h1>

        <p className="mt-2 text-slate-500">
          Arraste os clientes entre as etapas do processo comercial.
        </p>
      </header>

      <section className="mb-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Leads ativos
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-950">
            {ativos}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Fechados
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-950">
            {vendidos}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Perdidos
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-950">
            {perdidos}
          </p>
        </div>
      </section>

      <KanbanBoard
        initialLeads={leads}
      />
    </div>
  );
}