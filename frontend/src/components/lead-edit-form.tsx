"use client";

import { FormEvent, useState } from "react";
import { Pencil, Save, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { clientApi } from "@/lib/client-api";

type Campaign = { id: number; nome: string; canal: string };

type Lead = {
  id: number;
  nome: string;
  origem: string;
  objetivo: string;
  status: string;
  interesse: string;
  idade: number | null;
  genero: string | null;
  cidade: string | null;
  faixa_orcamento: string | null;
  tipo_cliente: string;
  empresa: string | null;
  cargo: string | null;
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
  campaign_id: number | null;
};

const stages = ["Lead", "Contato realizado", "Interessado", "Reunião", "Proposta", "Negociação", "Fechado", "Pós-venda", "Perdido"];

function localDateTime(value: string | null) {
  if (!value) return "";
  const d = new Date(value);
  const offset = d.getTimezoneOffset();
  return new Date(d.getTime() - offset * 60_000).toISOString().slice(0, 16);
}

export default function LeadEditForm({ lead, campaigns }: { lead: Lead; campaigns: Campaign[] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({
    nome: lead.nome,
    origem: lead.origem,
    objetivo: lead.objetivo,
    status: lead.status,
    interesse: lead.interesse,
    idade: lead.idade?.toString() ?? "",
    genero: lead.genero ?? "",
    cidade: lead.cidade ?? "",
    faixa_orcamento: lead.faixa_orcamento ?? "",
    tipo_cliente: lead.tipo_cliente,
    empresa: lead.empresa ?? "",
    cargo: lead.cargo ?? "",
    email: lead.email ?? "",
    telefone: lead.telefone ?? "",
    consentimento_contato: lead.consentimento_contato,
    segmento: lead.segmento ?? "",
    tamanho_equipe: lead.tamanho_equipe?.toString() ?? "",
    dor_gatilho: lead.dor_gatilho ?? "",
    proxima_acao: lead.proxima_acao ?? "",
    proxima_acao_em: localDateTime(lead.proxima_acao_em),
    motivo_perda: lead.motivo_perda ?? "",
    formato_interesse: lead.formato_interesse ?? "",
    oferta_interesse: lead.oferta_interesse ?? "",
    campaign_id: lead.campaign_id?.toString() ?? "",
  });

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    try {
      const response = await clientApi(`/api/leads/${lead.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          idade: form.idade ? Number(form.idade) : null,
          tamanho_equipe: form.tamanho_equipe ? Number(form.tamanho_equipe) : null,
          campaign_id: form.campaign_id ? Number(form.campaign_id) : null,
          genero: form.genero || null,
          cidade: form.cidade || null,
          faixa_orcamento: form.faixa_orcamento || null,
          empresa: form.empresa || null,
          cargo: form.cargo || null,
          email: form.email || null,
          telefone: form.telefone || null,
          segmento: form.segmento || null,
          dor_gatilho: form.dor_gatilho || null,
          proxima_acao: form.proxima_acao || null,
          proxima_acao_em: form.proxima_acao_em || null,
          motivo_perda: form.status === "Perdido" ? form.motivo_perda || null : null,
          formato_interesse: form.formato_interesse || null,
          oferta_interesse: form.oferta_interesse || null,
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        setMessage(data.detail ?? "Não foi possível atualizar o Lead.");
        return;
      }
      setMessage("Ficha atualizada com sucesso.");
      router.refresh();
    } catch {
      setMessage("Não foi possível conectar ao servidor.");
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return <button type="button" onClick={() => setOpen(true)} className="mt-6 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-ice"><Pencil size={16} />Editar ficha comercial</button>;
  }

  const input = "w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-cobalt-500";
  return <form onSubmit={submit} className="mt-6 rounded-card border border-cobalt-200 bg-cobalt-50/40 p-6">
    <div className="flex items-start justify-between gap-4"><div><h2 className="font-bold text-midnight">Editar ficha comercial</h2><p className="mt-1 text-sm text-slate-500">Atualize contexto, oferta, próxima ação e dados do relacionamento.</p></div><button type="button" onClick={() => setOpen(false)} className="rounded-lg p-2 hover:bg-white"><X size={18} /></button></div>
    <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Field label="Nome"><input required className={input} value={form.nome} onChange={(e) => set("nome", e.target.value)} /></Field>
      <Field label="Empresa"><input className={input} value={form.empresa} onChange={(e) => set("empresa", e.target.value)} /></Field>
      <Field label="Tipo"><select className={input} value={form.tipo_cliente} onChange={(e) => set("tipo_cliente", e.target.value)}><option>B2B</option><option>B2C</option></select></Field>
      <Field label="Etapa"><select className={input} value={form.status} onChange={(e) => set("status", e.target.value)}>{stages.map((x) => <option key={x}>{x}</option>)}</select></Field>
      <Field label="E-mail"><input type="email" className={input} value={form.email} onChange={(e) => set("email", e.target.value)} /></Field>
      <Field label="Telefone"><input className={input} value={form.telefone} onChange={(e) => set("telefone", e.target.value)} /></Field>
      <Field label="Cargo / área"><input className={input} value={form.cargo} onChange={(e) => set("cargo", e.target.value)} /></Field>
      <Field label="Segmento"><input className={input} value={form.segmento} onChange={(e) => set("segmento", e.target.value)} /></Field>
      <Field label="Tamanho da equipe"><input type="number" min="1" className={input} value={form.tamanho_equipe} onChange={(e) => set("tamanho_equipe", e.target.value)} /></Field>
      <Field label="Cidade"><input className={input} value={form.cidade} onChange={(e) => set("cidade", e.target.value)} /></Field>
      <Field label="Origem"><input required className={input} value={form.origem} onChange={(e) => set("origem", e.target.value)} /></Field>
      <Field label="Campanha"><select className={input} value={form.campaign_id} onChange={(e) => set("campaign_id", e.target.value)}><option value="">Sem campanha</option>{campaigns.map((c) => <option key={c.id} value={c.id}>{c.nome} · {c.canal}</option>)}</select></Field>
      <Field label="Objetivo"><input required className={input} value={form.objetivo} onChange={(e) => set("objetivo", e.target.value)} /></Field>
      <Field label="Interesse"><select className={input} value={form.interesse} onChange={(e) => set("interesse", e.target.value)}><option>Baixo</option><option>Médio</option><option>Alto</option></select></Field>
      <Field label="Oferta"><input className={input} value={form.oferta_interesse} onChange={(e) => set("oferta_interesse", e.target.value)} /></Field>
      <Field label="Formato"><input className={input} value={form.formato_interesse} onChange={(e) => set("formato_interesse", e.target.value)} /></Field>
      <Field label="Faixa de orçamento"><input className={input} value={form.faixa_orcamento} onChange={(e) => set("faixa_orcamento", e.target.value)} /></Field>
      <Field label="Próxima ação"><input className={input} value={form.proxima_acao} onChange={(e) => set("proxima_acao", e.target.value)} /></Field>
      <Field label="Data da próxima ação"><input type="datetime-local" className={input} value={form.proxima_acao_em} onChange={(e) => set("proxima_acao_em", e.target.value)} /></Field>
      <Field label="Gênero (opcional B2C)"><input className={input} value={form.genero} onChange={(e) => set("genero", e.target.value)} /></Field>
      <Field label="Idade (opcional B2C)"><input type="number" min="0" className={input} value={form.idade} onChange={(e) => set("idade", e.target.value)} /></Field>
      <div className="md:col-span-2 xl:col-span-4"><Field label="Dor / gatilho"><textarea rows={3} className={input} value={form.dor_gatilho} onChange={(e) => set("dor_gatilho", e.target.value)} /></Field></div>
      {form.status === "Perdido" && <div className="md:col-span-2 xl:col-span-4"><Field label="Motivo da perda"><textarea required rows={2} className={input} value={form.motivo_perda} onChange={(e) => set("motivo_perda", e.target.value)} /></Field></div>}
    </div>
    <label className="mt-4 flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={form.consentimento_contato} onChange={(e) => set("consentimento_contato", e.target.checked)} />Consentimento para contato registrado</label>
    {message && <p className="mt-4 text-sm font-medium text-slate-700">{message}</p>}
    <button disabled={saving} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-cobalt-500 transition hover:bg-cobalt-600 px-5 py-3 text-sm font-bold text-white disabled:opacity-50"><Save size={17} />{saving ? "Salvando..." : "Salvar alterações"}</button>
  </form>;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>{children}</label>;
}
