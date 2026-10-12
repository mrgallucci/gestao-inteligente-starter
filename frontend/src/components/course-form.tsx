"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap } from "lucide-react";
import { clientApi } from "@/lib/client-api";

export type CourseFormProduct = { id: number; nome: string; curso_id: number | null };

type Props = { products: CourseFormProduct[]; initialProductId?: number | null };

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-cobalt-500";

export default function CourseForm({ products, initialProductId = null }: Props) {
  const router = useRouter();
  // Relação 1 Produto → no máximo 1 Curso: só oferece produtos ainda sem curso.
  const available = products.filter((product) => product.curso_id === null);
  const preselected = available.some((product) => product.id === initialProductId)
    ? String(initialProductId)
    : "";

  const [productId, setProductId] = useState(preselected);
  const [nome, setNome] = useState("");
  const [descricao, setDescricao] = useState("");
  const [ativo, setAtivo] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState<{ tipo: "ok" | "erro"; texto: string } | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSalvando(true);
    setMensagem(null);
    try {
      const response = await clientApi("/api/courses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: Number(productId),
          nome,
          descricao: descricao || null,
          ativo,
        }),
      });
      if (response.status === 401) {
        router.replace("/login");
        return;
      }
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        setMensagem({
          tipo: "erro",
          texto: typeof data?.detail === "string" ? data.detail : "Não foi possível criar o curso.",
        });
        return;
      }
      setProductId("");
      setNome("");
      setDescricao("");
      setAtivo(true);
      setMensagem({ tipo: "ok", texto: "Curso criado e vinculado ao produto." });
      router.refresh();
    } catch {
      setMensagem({ tipo: "erro", texto: "Não foi possível conectar ao servidor." });
    } finally {
      setSalvando(false);
    }
  }

  if (available.length === 0) {
    return (
      <section className="mb-6 rounded-card border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-midnight">Novo curso</h2>
        <p className="mt-2 text-sm text-slate-500">
          Todos os produtos já possuem curso (cada produto libera no máximo um curso). Cadastre um novo
          produto em <a href="/products" className="font-semibold text-cobalt-600 underline">Produtos</a>{" "}
          para criar outro curso.
        </p>
      </section>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mb-6 rounded-card border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold text-midnight">Novo curso</h2>
      <p className="mt-1 text-sm text-slate-500">
        O curso é liberado automaticamente quando uma venda do produto vinculado é paga.
      </p>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="curso-produto" className="mb-2 block text-sm font-medium">Produto vinculado *</label>
          <select id="curso-produto" required value={productId} onChange={(e) => setProductId(e.target.value)} className={inputClass}>
            <option value="">Selecione um produto sem curso</option>
            {available.map((product) => (
              <option key={product.id} value={product.id}>{product.nome}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="curso-nome" className="mb-2 block text-sm font-medium">Nome do curso *</label>
          <input id="curso-nome" required maxLength={150} value={nome} onChange={(e) => setNome(e.target.value)} className={inputClass} />
        </div>
        <div className="md:col-span-2">
          <label htmlFor="curso-descricao" className="mb-2 block text-sm font-medium">Descrição</label>
          <textarea id="curso-descricao" rows={2} value={descricao} onChange={(e) => setDescricao(e.target.value)} className={inputClass} />
        </div>
        <div>
          <label htmlFor="curso-status" className="mb-2 block text-sm font-medium">Status</label>
          <select id="curso-status" value={ativo ? "ativo" : "inativo"} onChange={(e) => setAtivo(e.target.value === "ativo")} className={inputClass}>
            <option value="ativo">Ativo — libera acesso nas vendas pagas</option>
            <option value="inativo">Inativo — não libera acesso</option>
          </select>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-4">
        <button disabled={salvando} className="flex items-center gap-2 rounded-xl bg-cobalt-500 px-5 py-3 text-sm font-bold text-white transition hover:bg-cobalt-600 disabled:opacity-50">
          <GraduationCap size={18} />
          {salvando ? "Salvando..." : "Criar curso"}
        </button>
        {mensagem && (
          <p role="status" className={mensagem.tipo === "ok" ? "text-sm font-medium text-success" : "text-sm font-medium text-danger"}>
            {mensagem.texto}
          </p>
        )}
      </div>
    </form>
  );
}
