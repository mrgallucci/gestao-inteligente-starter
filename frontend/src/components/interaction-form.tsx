"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { CalendarClock, MessageSquarePlus } from "lucide-react";
import { clientApi } from "@/lib/client-api";

type Props = { leadId: number };

export default function InteractionForm({ leadId }: Props) {
  const router = useRouter();
  const [tipo, setTipo] = useState("WhatsApp");
  const [descricao, setDescricao] = useState("");
  const [resultado, setResultado] = useState("");
  const [followUpEm, setFollowUpEm] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSalvando(true);
    setMensagem("");

    try {
      const response = await clientApi(`/api/leads/${leadId}/interactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tipo, descricao, resultado: resultado || null, follow_up_em: followUpEm || null }),
      });

      if (response.status === 401) { router.replace("/login"); return; }
      if (!response.ok) { const data = await response.json().catch(() => null); setMensagem(data?.detail ?? "Não foi possível registrar o atendimento."); return; }

      setDescricao(""); setResultado(""); setFollowUpEm("");
      setMensagem("Atendimento registrado com sucesso!");
      router.refresh();
    } catch {
      setMensagem("Não foi possível conectar ao servidor.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5"><h2 className="text-lg font-bold text-midnight">Registrar atendimento</h2><p className="mt-1 text-sm text-slate-500">Registre contato, resultado e próximo retorno.</p></div>
      <div className="grid gap-4 md:grid-cols-2">
        <div><label className="mb-2 block text-sm font-medium text-slate-700">Tipo de contato</label><select value={tipo} onChange={(e) => setTipo(e.target.value)} className={inputClass}><option>WhatsApp</option><option>Ligação</option><option>E-mail</option><option>LinkedIn</option><option>Reunião</option><option>Follow-up</option><option>Observação</option></select></div>
        <div><label className="mb-2 block text-sm font-medium text-slate-700">Resultado</label><select value={resultado} onChange={(e) => setResultado(e.target.value)} className={inputClass}><option value="">Não informado</option><option>Interessado</option><option>Reunião agendada</option><option>Proposta solicitada</option><option>Aguardando retorno</option><option>Sem resposta</option><option>Não interessado</option><option>Negociação</option></select></div>
      </div>
      <div className="mt-4"><label className="mb-2 block text-sm font-medium text-slate-700">Descrição</label><textarea required rows={4} value={descricao} onChange={(e) => setDescricao(e.target.value)} placeholder="Ex.: equipe quer workshop de IA para comercial; diagnóstico agendado..." className={`${inputClass} resize-none`} /></div>
      <div className="mt-4 max-w-md"><label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700"><CalendarClock size={17} />Próximo follow-up</label><input type="datetime-local" value={followUpEm} onChange={(e) => setFollowUpEm(e.target.value)} className={inputClass} /></div>
      <div className="mt-5 flex items-center gap-4"><button type="submit" disabled={salvando} className="flex items-center gap-2 rounded-xl bg-cobalt-500 px-5 py-3 text-sm font-bold text-white transition hover:bg-cobalt-600 disabled:opacity-50"><MessageSquarePlus size={18} />{salvando ? "Registrando..." : "Registrar atendimento"}</button>{mensagem && <p className="text-sm text-slate-600">{mensagem}</p>}</div>
    </form>
  );
}

const inputClass = "w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cobalt-500";
