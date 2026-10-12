import { protectedJson } from "@/lib/server-protected";
import SaleForm from "@/components/sale-form";
import SaleStatusControl from "@/components/sale-status-control";

type Lead = {
  id: number;
  nome: string;
};

type Product = {
  id: number;
  nome: string;
  preco: number;
  ativo: boolean;
  curso_id: number | null;
  curso_nome: string | null;
  curso_ativo: boolean | null;
};

type Sale = {
  id: number;
  lead_nome: string;
  produto_nome: string;
  quantidade: number;
  valor_unitario: number;
  valor_total: number;
  forma_pagamento: string;
  status_pagamento: string;
  criado_em: string;
  entrega_tipo: "LMS" | null;
  entrega_status:
    | "Acesso liberado"
    | "Aguardando pagamento"
    | "Acesso suspenso"
    | "Matrícula não gerada"
    | "Não aplicável";
  entrega_detalhe: string;
  aviso: string | null;
  curso_nome: string | null;
  curso_ativo: boolean | null;
  matricula_status: string | null;
};

async function getData() {
  const [leads, products, sales] = await Promise.all([
    protectedJson<Lead[]>("/api/leads", "Erro ao carregar leads."),
    protectedJson<Product[]>("/api/products", "Erro ao carregar produtos."),
    protectedJson<Sale[]>("/api/sales", "Erro ao carregar vendas."),
  ]);

  return { leads, products, sales };
}

function deliveryStatusClass(status: Sale["entrega_status"]) {
  const base = "inline-block rounded-full px-2.5 py-1 text-xs font-semibold ";
  if (status === "Acesso liberado") return base + "bg-success/10 text-success";
  if (status === "Aguardando pagamento" || status === "Matrícula não gerada") return base + "bg-warning/10 text-warning";
  if (status === "Acesso suspenso") return base + "bg-danger/10 text-danger";
  return base + "bg-slate-100 text-slate-600";
}

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export default async function SalesPage() {
  const {
    leads,
    products,
    sales,
  } = await getData();

  const receita = sales
    .filter(
      (sale) =>
        sale.status_pagamento === "Pago"
    )
    .reduce(
      (total, sale) =>
        total + Number(sale.valor_total),
      0
    );

  return (
    <div className="mx-auto max-w-7xl">

      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-cobalt-600">
          Comercial
        </p>

        <h1 className="mt-1 text-3xl font-bold text-midnight">
          Vendas
        </h1>

        <p className="mt-2 text-slate-500">
          Registre e acompanhe as vendas realizadas.
        </p>
      </header>

      <section className="mb-6 grid gap-4 sm:grid-cols-2">

        <div className="rounded-card border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Vendas registradas
          </p>

          <p className="mt-2 text-3xl font-bold">
            {sales.length}
          </p>
        </div>

        <div className="rounded-card bg-midnight p-5 text-white shadow-sm">
          <p className="text-sm text-slate-400">
            Receita registrada
          </p>

          <p className="mt-2 text-3xl font-bold">
            {money.format(receita)}
          </p>
        </div>

      </section>

      <SaleForm
        leads={leads}
        products={products}
      />

      <section className="mt-6 overflow-hidden rounded-card border border-slate-200 bg-white shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[1100px] text-left text-sm">

            <thead className="bg-ice text-xs uppercase text-slate-500">
              <tr>
                <th className="px-5 py-4">
                  Cliente
                </th>
                <th className="px-5 py-4">
                  Produto
                </th>
                <th className="px-5 py-4">
                  Qtd.
                </th>
                <th className="px-5 py-4">
                  Total
                </th>
                <th className="px-5 py-4">
                  Pagamento
                </th>
                <th className="px-5 py-4">
                  Status
                </th>
                <th className="px-5 py-4">
                  Entrega
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">

              {sales.map((sale) => (
                <tr key={sale.id}>

                  <td className="px-5 py-4 font-semibold">
                    {sale.lead_nome}
                  </td>

                  <td className="px-5 py-4">
                    {sale.produto_nome}
                  </td>

                  <td className="px-5 py-4">
                    {sale.quantidade}
                  </td>

                  <td className="px-5 py-4 font-bold">
                    {money.format(
                      Number(
                        sale.valor_total
                      )
                    )}
                  </td>

                  <td className="px-5 py-4">
                    {sale.forma_pagamento}
                  </td>

                  <td className="px-5 py-4">
                    <SaleStatusControl saleId={sale.id} initialStatus={sale.status_pagamento} />
                  </td>

                  <td className="px-5 py-4">
                    <div className="flex flex-wrap items-center gap-2">
                      {sale.entrega_tipo && (
                        <span className="inline-block rounded-full bg-cobalt-50 px-2.5 py-1 text-xs font-semibold text-cobalt-700">
                          {sale.entrega_tipo}
                        </span>
                      )}
                      <span className={deliveryStatusClass(sale.entrega_status)}>
                        {sale.entrega_status}
                      </span>
                    </div>
                    {sale.curso_nome && (
                      <p className="mt-1 text-xs text-slate-500">{sale.curso_nome}</p>
                    )}
                    <p className="mt-1 text-xs text-slate-400">{sale.entrega_detalhe}</p>
                    {sale.aviso && (
                      <p className="mt-1 text-xs font-semibold text-warning">⚠ {sale.aviso}</p>
                    )}
                  </td>
                </tr>
              ))}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  );
}