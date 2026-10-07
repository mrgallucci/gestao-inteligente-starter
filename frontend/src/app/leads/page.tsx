import LeadForm from "@/components/lead-form";
import LeadList from "@/components/lead-list";
import { protectedJson } from "@/lib/server-protected";

type Campaign = { id: number; nome: string; canal: string; ativo: boolean };
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

async function getLeads() { return protectedJson<Lead[]>("/api/leads", "Não foi possível carregar os leads."); }
async function getCampaigns() { return protectedJson<Campaign[]>("/api/campaigns", "Não foi possível carregar as campanhas."); }

export default async function LeadsPage() {
  const [leads, campaigns] = await Promise.all([getLeads(), getCampaigns()]);
  return <div className="mx-auto max-w-7xl">
    <header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">CRM</p><h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">Leads</h1><p className="mt-2 text-slate-500">CRM atualizado para o pipeline comercial do SargLab — IA no Dia a Dia.</p></header>
    <LeadForm campaigns={campaigns} />
    <LeadList leads={leads} />
  </div>;
}
