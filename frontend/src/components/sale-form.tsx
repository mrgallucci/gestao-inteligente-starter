"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ShoppingCart } from "lucide-react";
import { clientApi } from "@/lib/client-api";

type Lead = { id: number; nome: string };
type Product = {
  id: number;
  nome: string;
  preco: number;
  ativo: boolean;
  curso_id?: number | null;
  curso_nome?: string | null;
  curso_ativo?: boolean | null;
};
type Props = { leads: Lead[]; products: Product[] };

export default function SaleForm({ leads, products }: Props) {
  const router = useRouter();
  const [leadId, setLeadId] = useState("");
  const [productId, setProductId] = useState("");
  const [quantidade, setQuantidade] = useState(1);
  const [pagamento, setPagamento] = useState("Pix");
  const [statusPagamento, setStatusPagamento] = useState("Pago");
  const [salvando, setSalvando] = useState(false);
  const [mensagem, setMensagem] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSalvando(true); setMensagem("");
    try {
      const response = await clientApi("/api/sales", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ lead_id: Number(leadId), product_id: Number(productId), quantidade, forma_pagamento: pagamento, status_pagamento: statusPagamento }) });
      if (response.status === 401) { router.replace("/login"); return; }
      if (!response.ok) { const data = await response.json().catch(() => null); setMensagem(data?.detail ?? "Não foi possível registrar a venda."); return; }
      setQuantidade(1); setMensagem("Venda registrada com sucesso!"); router.refresh();
    } catch { setMensagem("Não foi possível conectar ao servidor."); }
    finally { setSalvando(false); }
  }

  const selectedProduct = products.find((product) => String(product.id) === productId);
  const selectedLead = leads.find((lead) => String(lead.id) === leadId);
  const delivery = describeDelivery(selectedProduct, statusPagamento, selectedLead?.nome);

  return <form onSubmit={handleSubmit} className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">
    <h2 className="text-lg font-bold text-midnight">Registrar venda</h2><p className="mt-1 text-sm text-slate-500">Vendas pagas movem o Lead para Fechado e liberam matrícula quando houver curso associado.</p>
    <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <Field label="Cliente"><select required value={leadId} onChange={(e) => setLeadId(e.target.value)} className={inputClass}><option value="">Selecione</option>{leads.map((lead) => <option key={lead.id} value={lead.id}>{lead.nome}</option>)}</select></Field>
      <Field label="Produto"><select required value={productId} onChange={(e) => setProductId(e.target.value)} className={inputClass}><option value="">Selecione</option>{products.filter((p) => p.ativo).map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select></Field>
      <Field label="Quantidade"><input type="number" min="1" value={quantidade} onChange={(e) => setQuantidade(Number(e.target.value))} className={inputClass} /></Field>
      <Field label="Pagamento"><select value={pagamento} onChange={(e) => setPagamento(e.target.value)} className={inputClass}><option>Pix</option><option>Cartão</option><option>Boleto</option><option>Transferência</option><option>Dinheiro</option></select></Field>
      <Field label="Status"><select value={statusPagamento} onChange={(e) => setStatusPagamento(e.target.value)} className={inputClass}><option>Pago</option><option>Pendente</option><option>Cancelado</option><option>Reembolsado</option></select></Field>
    </div>
    {delivery && <div role="status" aria-live="polite" className={["mt-5 rounded-xl border p-4 text-sm", delivery.warn ? "border-warning/40 bg-warning/10 text-warning" : delivery.lms ? "border-cobalt-200 bg-cobalt-50 text-cobalt-900" : "border-slate-200 bg-ice text-slate-700"].join(" ")}><p className="font-semibold">{delivery.titulo}</p><p className="mt-1">{delivery.texto}</p></div>}
    <div className="mt-5 flex items-center gap-4"><button disabled={salvando} className="flex items-center gap-2 rounded-xl bg-cobalt-500 transition hover:bg-cobalt-600 px-5 py-3 text-sm font-bold text-white disabled:opacity-50"><ShoppingCart size={18} />{salvando ? "Registrando..." : "Registrar venda"}</button>{mensagem && <p className="text-sm text-slate-600">{mensagem}</p>}</div>
  </form>;
}

type Delivery = { lms: boolean; warn?: boolean; titulo: string; texto: string };

function describeDelivery(product: Product | undefined, status: string, leadName?: string): Delivery | null {
  if (!product) return null;
  if (product.curso_id == null) {
    return { lms: false, titulo: "Sem liberação de LMS", texto: "Este produto não libera curso. A venda será registrada normalmente, sem matrícula." };
  }
  if (!product.curso_ativo) {
    return { lms: false, warn: true, titulo: "Atenção: curso inativo", texto: `O curso “${product.curso_nome}” está inativo. A venda pode ser registrada, mas NÃO gerará matrícula nem acesso ao LMS.` };
  }
  const quem = leadName ? ` para ${leadName}` : "";
  if (status === "Pago") {
    return { lms: true, titulo: "Esta venda liberará acesso ao LMS", texto: `Ao confirmar, o curso “${product.curso_nome}” será concedido${quem} (matrícula automática).` };
  }
  if (status === "Pendente") {
    return { lms: true, titulo: "Acesso ao LMS após o pagamento", texto: `O curso “${product.curso_nome}” será liberado quando o status for alterado para Pago.` };
  }
  return { lms: false, titulo: "Sem liberação de LMS", texto: `Com pagamento ${status.toLowerCase()}, o curso “${product.curso_nome}” não será liberado.` };
}

const inputClass = "w-full rounded-xl border border-slate-200 px-4 py-3";
function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="block"><span className="mb-2 block text-sm font-medium">{label}</span>{children}</label>; }
