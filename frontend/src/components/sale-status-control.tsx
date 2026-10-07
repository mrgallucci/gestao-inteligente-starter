"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { clientApi } from "@/lib/client-api";

export default function SaleStatusControl({ saleId, initialStatus }: { saleId: number; initialStatus: string }) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [saving, setSaving] = useState(false);

  async function update(nextStatus: string) {
    setStatus(nextStatus);
    setSaving(true);
    const response = await clientApi(`/api/sales/${saleId}/payment-status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status_pagamento: nextStatus }),
    });

    if (!response.ok) {
      setStatus(initialStatus);
      alert("Não foi possível atualizar o pagamento.");
    } else {
      router.refresh();
    }
    setSaving(false);
  }

  return <select value={status} disabled={saving} onChange={(e) => update(e.target.value)} className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-semibold">
    <option>Pago</option><option>Pendente</option><option>Cancelado</option><option>Reembolsado</option>
  </select>;
}
