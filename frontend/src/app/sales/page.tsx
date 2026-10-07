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
};

async function getData() {
  const [leads, products, sales] = await Promise.all([
    protectedJson<Lead[]>("/api/leads", "Erro ao carregar leads."),
    protectedJson<Product[]>("/api/products", "Erro ao carregar produtos."),
    protectedJson<Sale[]>("/api/sales", "Erro ao carregar vendas."),
  ]);

  return { leads, products, sales };
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
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Comercial
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-950">
          Vendas
        </h1>

        <p className="mt-2 text-slate-500">
          Registre e acompanhe as vendas realizadas.
        </p>
      </header>

      <section className="mb-6 grid gap-4 sm:grid-cols-2">

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">
            Vendas registradas
          </p>

          <p className="mt-2 text-3xl font-bold">
            {sales.length}
          </p>
        </div>

        <div className="rounded-2xl bg-slate-950 p-5 text-white shadow-sm">
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

      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[900px] text-left text-sm">

            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
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

                </tr>
              ))}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  );
}