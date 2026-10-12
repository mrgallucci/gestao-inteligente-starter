"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Megaphone } from "lucide-react";
import { clientApi } from "@/lib/client-api";

export default function CampaignForm() {
  const router = useRouter();
  const [nome, setNome] = useState("");
  const [canal, setCanal] = useState("Instagram");
  const [descricao, setDescricao] = useState("");
  const [custo, setCusto] = useState("0");
  const [utmSource, setUtmSource] = useState("instagram");
  const [utmMedium, setUtmMedium] = useState("social");
  const [utmCampaign, setUtmCampaign] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSalvando(true); setMensagem("");
    try {
      const response = await clientApi("/api/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, canal, descricao: descricao || null, custo: Number(custo || 0), ativo: true, utm_source: utmSource || null, utm_medium: utmMedium || null, utm_campaign: utmCampaign || null }),
      });
      if (response.status === 401) { router.replace("/login"); return; }
      if (!response.ok) { const data = await response.json().catch(() => null); setMensagem(data?.detail ?? "Não foi possível criar a campanha."); return; }
      setNome(""); setDescricao(""); setCusto("0"); setUtmCampaign(""); setMensagem("Campanha criada com sucesso!"); router.refresh();
    } catch { setMensagem("Não foi possível conectar ao servidor."); }
    finally { setSalvando(false); }
  }

  return <form onSubmit={handleSubmit} className="mb-6 rounded-card border border-slate-200 bg-white p-6 shadow-sm">
    <div className="flex items-center gap-3"><div className="rounded-xl bg-cobalt-50 p-3 text-cobalt-600"><Megaphone size={22} /></div><div><h2 className="font-bold text-midnight">Nova campanha</h2><p className="text-sm text-slate-500">Use UTM para tornar Instagram e outras origens mensuráveis no CRM.</p></div></div>
    <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Field label="Nome"><input required value={nome} onChange={(e) => setNome(e.target.value)} className={inputClass} placeholder="Lançamento SargLab" /></Field>
      <Field label="Canal"><select value={canal} onChange={(e) => setCanal(e.target.value)} className={inputClass}><option>Instagram</option><option>LinkedIn</option><option>Google</option><option>WhatsApp</option><option>E-mail</option><option>Evento</option><option>Outro</option></select></Field>
      <Field label="Custo"><input type="number" min="0" step="0.01" value={custo} onChange={(e) => setCusto(e.target.value)} className={inputClass} /></Field>
      <Field label="UTM campaign"><input value={utmCampaign} onChange={(e) => setUtmCampaign(e.target.value)} className={inputClass} placeholder="sarglab_lancamento" /></Field>
      <Field label="UTM source"><input value={utmSource} onChange={(e) => setUtmSource(e.target.value)} className={inputClass} /></Field>
      <Field label="UTM medium"><input value={utmMedium} onChange={(e) => setUtmMedium(e.target.value)} className={inputClass} /></Field>
      <div className="md:col-span-2"><Field label="Descrição"><input value={descricao} onChange={(e) => setDescricao(e.target.value)} className={inputClass} placeholder="Objetivo e público da campanha" /></Field></div>
    </div>
    <div className="mt-5 flex items-center gap-4"><button disabled={salvando} className="rounded-xl bg-cobalt-500 transition hover:bg-cobalt-600 px-5 py-3 text-sm font-bold text-white disabled:opacity-50">{salvando ? "Salvando..." : "Criar campanha"}</button>{mensagem && <p className="text-sm text-slate-600">{mensagem}</p>}</div>
  </form>;
}
const inputClass = "w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-cobalt-500";
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <div><label className="mb-2 block text-sm font-medium text-slate-700">{label}</label>{children}</div>; }
