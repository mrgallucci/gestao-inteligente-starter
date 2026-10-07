"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { PackagePlus } from "lucide-react";
import { clientApi } from "@/lib/client-api";

export default function ProductForm() {
  const router = useRouter();
  const [nome, setNome] = useState("");
  const [descricao, setDescricao] = useState("");
  const [preco, setPreco] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSalvando(true); setMensagem("");
    try {
      const response = await clientApi("/api/products", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome, descricao: descricao || null, preco: Number(preco), ativo: true }) });
      if (response.status === 401) { router.replace("/login"); return; }
      if (!response.ok) { const data = await response.json().catch(() => null); setMensagem(data?.detail ?? "Erro ao cadastrar produto."); return; }
      setNome(""); setDescricao(""); setPreco(""); setMensagem("Produto cadastrado!"); router.refresh();
    } catch { setMensagem("Não foi possível conectar ao servidor."); }
    finally { setSalvando(false); }
  }

  return <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <h2 className="text-lg font-bold text-slate-950">Novo produto</h2><p className="mt-1 text-sm text-slate-500">Cadastre workshops, cursos, serviços ou materiais digitais.</p>
    <div className="mt-5 grid gap-4 md:grid-cols-3"><div><label className="mb-2 block text-sm font-medium">Nome</label><input required value={nome} onChange={(e) => setNome(e.target.value)} className={inputClass} /></div><div><label className="mb-2 block text-sm font-medium">Preço</label><input required type="number" step="0.01" min="0" value={preco} onChange={(e) => setPreco(e.target.value)} placeholder="147.00" className={inputClass} /></div><div><label className="mb-2 block text-sm font-medium">Descrição</label><input value={descricao} onChange={(e) => setDescricao(e.target.value)} className={inputClass} /></div></div>
    <div className="mt-5 flex items-center gap-4"><button disabled={salvando} className="flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-sm font-bold text-slate-950 disabled:opacity-50"><PackagePlus size={18} />{salvando ? "Salvando..." : "Cadastrar produto"}</button>{mensagem && <p className="text-sm text-slate-600">{mensagem}</p>}</div>
  </form>;
}
const inputClass = "w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500";
