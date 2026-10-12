"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus } from "lucide-react";

import { clientApi } from "@/lib/client-api";

type Campaign = {
  id: number;
  nome: string;
  canal: string;
  ativo: boolean;
};

type Props = {
  campaigns: Campaign[];
};

export default function LeadForm({ campaigns }: Props) {
  const router = useRouter();

  const [nome, setNome] = useState("");
  const [tipoCliente, setTipoCliente] = useState("B2B");
  const [origem, setOrigem] = useState("Instagram @sarglab.ia");
  const [objetivo, setObjetivo] = useState("");
  const [interesse, setInteresse] = useState("Médio");
  const [empresa, setEmpresa] = useState("");
  const [cargo, setCargo] = useState("");
  const [email, setEmail] = useState("");
  const [telefone, setTelefone] = useState("");
  const [consentimento, setConsentimento] = useState(false);
  const [segmento, setSegmento] = useState("");
  const [tamanhoEquipe, setTamanhoEquipe] = useState("");
  const [dorGatilho, setDorGatilho] = useState("");
  const [proximaAcao, setProximaAcao] = useState("");
  const [proximaAcaoEm, setProximaAcaoEm] = useState("");
  const [formatoInteresse, setFormatoInteresse] = useState("Online ao vivo");
  const [ofertaInteresse, setOfertaInteresse] = useState("SargLab — IA no Trabalho | B2B");
  const [cidade, setCidade] = useState("");
  const [idade, setIdade] = useState("");
  const [genero, setGenero] = useState("");
  const [faixaOrcamento, setFaixaOrcamento] = useState("");
  const [campaignId, setCampaignId] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSalvando(true);
    setMensagem("");

    try {
      const response = await clientApi("/api/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nome,
          origem,
          objetivo,
          status: "Lead",
          interesse,
          tipo_cliente: tipoCliente,
          empresa: empresa || null,
          cargo: cargo || null,
          email: email || null,
          telefone: telefone || null,
          consentimento_contato: consentimento,
          segmento: segmento || null,
          tamanho_equipe: tamanhoEquipe ? Number(tamanhoEquipe) : null,
          dor_gatilho: dorGatilho || null,
          proxima_acao: proximaAcao || null,
          proxima_acao_em: proximaAcaoEm || null,
          formato_interesse: formatoInteresse || null,
          oferta_interesse: ofertaInteresse || null,
          idade: idade ? Number(idade) : null,
          genero: genero || null,
          cidade: cidade || null,
          faixa_orcamento: faixaOrcamento || null,
          campaign_id: campaignId ? Number(campaignId) : null,
        }),
      });

      if (response.status === 401) {
        router.replace("/login");
        return;
      }

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setMensagem(data?.detail ?? "Erro ao cadastrar Lead.");
        return;
      }

      setNome("");
      setEmpresa("");
      setCargo("");
      setEmail("");
      setTelefone("");
      setConsentimento(false);
      setSegmento("");
      setTamanhoEquipe("");
      setDorGatilho("");
      setProximaAcao("");
      setProximaAcaoEm("");
      setCidade("");
      setIdade("");
      setGenero("");
      setFaixaOrcamento("");
      setCampaignId("");
      setObjetivo("");
      setMensagem("Lead cadastrado com sucesso!");
      router.refresh();
    } catch {
      setMensagem("Não foi possível conectar ao servidor.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mb-6 rounded-card border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-bold text-midnight">Cadastrar novo Lead</h2>
        <p className="mt-1 text-sm text-slate-500">
          Pipeline SargLab: Lead → Contato realizado → Interessado → Reunião → Proposta → Negociação → Fechado → Pós-venda.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Field label="Nome"><input required value={nome} onChange={(e) => setNome(e.target.value)} className={inputClass} placeholder="Nome do contato" /></Field>
        <Field label="Tipo"><select value={tipoCliente} onChange={(e) => setTipoCliente(e.target.value)} className={inputClass}><option>B2B</option><option>B2C</option></select></Field>
        <Field label="Empresa"><input value={empresa} onChange={(e) => setEmpresa(e.target.value)} className={inputClass} placeholder="Empresa / organização" /></Field>
        <Field label="Cargo"><input value={cargo} onChange={(e) => setCargo(e.target.value)} className={inputClass} placeholder="Ex.: RH, Comercial" /></Field>

        <Field label="E-mail"><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className={inputClass} /></Field>
        <Field label="Telefone / WhatsApp"><input value={telefone} onChange={(e) => setTelefone(e.target.value)} className={inputClass} /></Field>
        <Field label="Origem"><select value={origem} onChange={(e) => setOrigem(e.target.value)} className={inputClass}><option>Instagram @sarglab.ia</option><option>Landing page</option><option>WhatsApp</option><option>LinkedIn</option><option>Indicação</option><option>Google</option><option>Evento</option><option>Outro</option></select></Field>
        <Field label="Campanha"><select value={campaignId} onChange={(e) => setCampaignId(e.target.value)} className={inputClass}><option value="">Sem campanha</option>{campaigns.filter((c) => c.ativo).map((c) => <option key={c.id} value={c.id}>{c.nome} — {c.canal}</option>)}</select></Field>

        <Field label="Oferta de interesse"><select value={ofertaInteresse} onChange={(e) => setOfertaInteresse(e.target.value)} className={inputClass}><option>SargLab — IA no Trabalho | B2B</option><option>SargLab — IA no Dia a Dia | Online</option><option>SargLab — IA no Dia a Dia | Presencial</option><option>Starter Kit SargLab — 60 prompts</option><option>Outro</option></select></Field>
        <Field label="Formato"><select value={formatoInteresse} onChange={(e) => setFormatoInteresse(e.target.value)} className={inputClass}><option>Online ao vivo</option><option>Presencial</option><option>Digital</option><option>A definir</option></select></Field>
        <Field label="Segmento"><input value={segmento} onChange={(e) => setSegmento(e.target.value)} className={inputClass} placeholder="Ex.: varejo, serviços" /></Field>
        <Field label="Tamanho da equipe"><input type="number" min="1" value={tamanhoEquipe} onChange={(e) => setTamanhoEquipe(e.target.value)} className={inputClass} placeholder="Ex.: 25" /></Field>

        <Field label="Objetivo"><input required value={objetivo} onChange={(e) => setObjetivo(e.target.value)} className={inputClass} placeholder="O que quer melhorar com IA?" /></Field>
        <Field label="Interesse"><select value={interesse} onChange={(e) => setInteresse(e.target.value)} className={inputClass}><option>Baixo</option><option>Médio</option><option>Alto</option></select></Field>
        <Field label="Cidade"><input value={cidade} onChange={(e) => setCidade(e.target.value)} className={inputClass} /></Field>
        <Field label="Faixa de orçamento"><select value={faixaOrcamento} onChange={(e) => setFaixaOrcamento(e.target.value)} className={inputClass}><option value="">Não informado</option><option>Até R$ 100</option><option>R$ 101 a R$ 500</option><option>R$ 501 a R$ 1.000</option><option>R$ 1.001 a R$ 2.000</option><option>Acima de R$ 2.000</option></select></Field>

        {tipoCliente === "B2C" && <><Field label="Idade"><input type="number" min="0" max="120" value={idade} onChange={(e) => setIdade(e.target.value)} className={inputClass} /></Field><Field label="Gênero"><select value={genero} onChange={(e) => setGenero(e.target.value)} className={inputClass}><option value="">Não informado</option><option>Feminino</option><option>Masculino</option><option>Outro</option><option>Prefere não informar</option></select></Field></>}

        <div className="md:col-span-2 xl:col-span-4"><Field label="Dor / gatilho"><textarea rows={3} value={dorGatilho} onChange={(e) => setDorGatilho(e.target.value)} className={inputClass} placeholder="Ex.: equipe já usa IA sem padrão, medo de expor dados, retrabalho em propostas..." /></Field></div>
        <div className="md:col-span-2"><Field label="Próxima ação"><input value={proximaAcao} onChange={(e) => setProximaAcao(e.target.value)} className={inputClass} placeholder="Ex.: agendar diagnóstico com RH" /></Field></div>
        <Field label="Data da próxima ação"><input type="datetime-local" value={proximaAcaoEm} onChange={(e) => setProximaAcaoEm(e.target.value)} className={inputClass} /></Field>
        <div className="flex items-end"><label className="flex items-center gap-2 pb-3 text-sm font-medium text-slate-700"><input type="checkbox" checked={consentimento} onChange={(e) => setConsentimento(e.target.checked)} />Consentimento para contato</label></div>
      </div>

      <div className="mt-6 flex items-center gap-4">
        <button type="submit" disabled={salvando} className="flex items-center gap-2 rounded-xl bg-cobalt-500 px-5 py-3 text-sm font-bold text-white transition hover:bg-cobalt-600 disabled:opacity-50"><Plus size={18} />{salvando ? "Salvando..." : "Cadastrar Lead"}</button>
        {mensagem && <p className="text-sm text-slate-600">{mensagem}</p>}
      </div>
    </form>
  );
}

const inputClass = "w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cobalt-500";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block"><span className="mb-2 block text-sm font-medium text-slate-700">{label}</span>{children}</label>;
}
