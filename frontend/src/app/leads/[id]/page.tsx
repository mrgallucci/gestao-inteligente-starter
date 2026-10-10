import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  CalendarClock,
  CircleUserRound,
  Mail,
  MessageCircle,
  Phone,
  ShieldCheck,
  Target,
  TrendingUp,
  UsersRound,
} from "lucide-react";

import InteractionForm from "@/components/interaction-form";
import LeadEditForm from "@/components/lead-edit-form";
import { protectedJson } from "@/lib/server-protected";
import { serverApi } from "@/lib/server-api";

type Lead = {
  id: number;
  nome: string;
  origem: string;
  objetivo: string;
  status: string;
  interesse: string;
  contatos: number;
  criado_em: string;
  tipo_cliente: string;
  empresa: string | null;
  cargo: string | null;
  area_profissional: string | null;
  email: string | null;
  telefone: string | null;
  consentimento_contato: boolean;
  segmento: string | null;
  tamanho_equipe: number | null;
  dor_gatilho: string | null;
  proxima_acao: string | null;
  proxima_acao_em: string | null;
  motivo_perda: string | null;
  formato_interesse: string | null;
  oferta_interesse: string | null;
  cidade: string | null;
  faixa_orcamento: string | null;
  idade: number | null;
  genero: string | null;
  campaign_id: number | null;
};

type Campaign = { id: number; nome: string; canal: string };

type Interaction = {
  id: number;
  lead_id: number;
  tipo: string;
  descricao: string;
  resultado: string | null;
  follow_up_em: string | null;
  criado_em: string;
};

async function getLead(id: string): Promise<Lead | null> {
  const response = await serverApi(`/api/leads/${id}`);
  if (response.status === 404) return null;
  if (response.status === 401 || response.status === 403) {
    return protectedJson<Lead>(`/api/leads/${id}`, "Erro ao carregar o lead.");
  }
  if (!response.ok) throw new Error("Erro ao carregar o lead.");
  return response.json();
}

async function getInteractions(id: string): Promise<Interaction[]> {
  return protectedJson<Interaction[]>(`/api/leads/${id}/interactions`, "Erro ao carregar o histórico.");
}

async function getCampaigns(): Promise<Campaign[]> {
  return protectedJson<Campaign[]>("/api/campaigns", "Erro ao carregar campanhas.");
}

type Props = { params: Promise<{ id: string }> };

export default async function LeadPage({ params }: Props) {
  const { id } = await params;
  const lead = await getLead(id);
  if (!lead) notFound();
  const [interactions, campaigns] = await Promise.all([getInteractions(id), getCampaigns()]);

  return <div className="mx-auto max-w-7xl">
    <Link href="/leads" className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900"><ArrowLeft size={18} />Voltar para Leads</Link>

    <header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">CRM / Lead #{lead.id}</p><h1 className="mt-2 text-3xl font-bold text-slate-950">{lead.nome}</h1><p className="mt-2 text-slate-500">
  Ficha comercial, interesses e histórico do relacionamento com a SargLab.
</p></header>

    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card icon={<CircleUserRound />} label="Origem" value={lead.origem} />
      <Card icon={<Target />} label="Objetivo" value={lead.objetivo} />
      <Card icon={<TrendingUp />} label="Etapa" value={lead.status} />
      <Card icon={<MessageCircle />} label="Contatos" value={String(lead.contatos)} />
    </section>

    <section className="mt-6 grid gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-950">Dados comerciais</h2>
        <dl className="mt-5 grid gap-4 sm:grid-cols-2">
          <Info icon={<Building2 size={17} />} label="Empresa" value={lead.empresa ?? "—"} />
          <Info icon={<UsersRound size={17} />} label="Tipo / equipe" value={`${lead.tipo_cliente}${lead.tamanho_equipe ? ` · ${lead.tamanho_equipe} pessoas` : ""}`} />
          <Info icon={<Mail size={17} />} label="E-mail" value={lead.email ?? "—"} />
          <Info icon={<Phone size={17} />} label="Telefone" value={lead.telefone ?? "—"} />
          <Info label="Cargo / área" value={ lead.cargo && lead.area_profissional? `${lead.cargo} · ${lead.area_profissional}`: lead.cargo ?? lead.area_profissional ?? "—"
  }
/>
          <Info label="Segmento" value={lead.segmento ?? "—"} />
          <Info label="Cidade" value={lead.cidade ?? "—"} />
          <Info label="Orçamento" value={lead.faixa_orcamento ?? "—"} />
          <Info label="Oferta" value={lead.oferta_interesse ?? "—"} />
          <Info label="Formato" value={lead.formato_interesse ?? "—"} />
        </dl>
        <div className="mt-5 flex items-center gap-2 text-sm"><ShieldCheck size={17} className={lead.consentimento_contato ? "text-emerald-600" : "text-slate-400"} /><span className="text-slate-600">Consentimento para contato: <strong>{lead.consentimento_contato ? "Sim" : "Não"}</strong></span></div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-950">Diagnóstico e próxima ação</h2>
        <div className="mt-5 space-y-5">
          <div><p className="text-sm text-slate-500">Dor / gatilho</p><p className="mt-1 whitespace-pre-wrap font-medium text-slate-900">{lead.dor_gatilho ?? "Não informado"}</p></div>
          <div><p className="text-sm text-slate-500">Próxima ação</p><p className="mt-1 font-medium text-slate-900">{lead.proxima_acao ?? "Não definida"}</p></div>
          <div className="flex items-center gap-2"><CalendarClock size={17} className="text-slate-400" /><p className="text-sm text-slate-600">{lead.proxima_acao_em ? new Date(lead.proxima_acao_em).toLocaleString("pt-BR") : "Sem data definida"}</p></div>
          {lead.status === "Perdido" && <div className="rounded-xl bg-red-50 p-4"><p className="text-sm font-semibold text-red-700">Motivo da perda</p><p className="mt-1 text-sm text-red-700">{lead.motivo_perda ?? "Não informado"}</p></div>}
        </div>
      </div>
    </section>

    <LeadEditForm lead={lead} campaigns={campaigns} />

    <section className="mt-6 grid gap-6 lg:grid-cols-[1fr_2fr]">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-lg font-bold text-slate-950">Relacionamento</h2><p className="mt-5 text-sm text-slate-500">Interações registradas</p><p className="mt-1 text-3xl font-bold text-slate-950">{interactions.length}</p><p className="mt-6 text-xs text-slate-400">Entrada no CRM: {new Date(lead.criado_em).toLocaleString("pt-BR")}</p></div>
      <InteractionForm leadId={lead.id} />
    </section>

    <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-950">Histórico de atendimento</h2>
      {interactions.length === 0 ? <div className="mt-5 rounded-xl bg-slate-50 p-5 text-sm text-slate-500">Nenhum atendimento registrado ainda.</div> : <div className="mt-5 space-y-4">{interactions.map((interaction) => <div key={interaction.id} className="rounded-xl border border-slate-200 p-4"><div className="flex items-start justify-between gap-4"><div><p className="font-bold text-slate-900">{interaction.tipo}</p><p className="mt-2 text-sm leading-relaxed text-slate-600">{interaction.descricao}</p></div><span className="shrink-0 text-xs text-slate-400">{new Date(interaction.criado_em).toLocaleString("pt-BR")}</span></div>{interaction.resultado && <div className="mt-4"><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">{interaction.resultado}</span></div>}{interaction.follow_up_em && <p className="mt-3 text-xs text-slate-500">Follow-up: {new Date(interaction.follow_up_em).toLocaleString("pt-BR")}</p>}</div>)}</div>}
    </section>
  </div>;
}

function Card({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) { return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-3 text-slate-500">{icon}</div><p className="text-xs uppercase text-slate-400">{label}</p><p className="mt-1 font-bold text-slate-900">{value}</p></div>; }
function Info({ icon, label, value }: { icon?: React.ReactNode; label: string; value: string }) { return <div><dt className="flex items-center gap-2 text-xs uppercase text-slate-400">{icon}{label}</dt><dd className="mt-1 font-medium text-slate-900">{value}</dd></div>; }
