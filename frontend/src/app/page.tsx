import {
  Activity,
  Banknote,
  CalendarClock,
  MessageSquare,
  Percent,
  PhoneCall,
  ReceiptText,
  ShoppingCart,
  UserX,
  Users,
} from "lucide-react";

import MetricCard from "@/components/metric-card";
import {
  serverApi,
} from "@/lib/server-api";
import {
  redirect,
} from "next/navigation";
import {
  getHomeForRole,
} from "@/lib/permissions";


type StatusData = {
  status: string;
  total: number;
};

type OriginData = {
  origem: string;
  total: number;
};

type ProductData = {
  product_id: number;
  produto: string;
  vendas: number;
  receita: number;
};

type RevenueOriginData = {
  origem: string;
  receita: number;
};

type ConversionOriginData = {
  origem: string;
  leads: number;
  convertidos: number;
  conversao: number;
};

type DashboardSummary = {
  total_leads: number;
  leads_ativos: number;
  fechados: number;
  perdidos: number;
  taxa_conversao: number;

  total_contatos: number;
  total_interacoes: number;
  followups_agendados: number;

  vendas_pagas: number;
  receita_total: number;
  ticket_medio: number;

  por_status: StatusData[];
  por_origem: OriginData[];
  por_produto: ProductData[];
  receita_por_origem: RevenueOriginData[];
  conversao_por_origem: ConversionOriginData[];
};


async function getDashboardSummary():
  Promise<DashboardSummary> {

  const response = await serverApi(
  "/api/dashboard/summary"
);
if (response.status === 401) {
  redirect("/login");
}


if (response.status === 403) {
  const meResponse =
    await serverApi(
      "/api/auth/me"
    );


  if (meResponse.ok) {
    const me =
      await meResponse.json();

    redirect(
      getHomeForRole(
        me.role
      )
    );
  }


  redirect("/login");
}


if (!response.ok) {
  throw new Error(
    "Não foi possível carregar o Dashboard."
  );
}

  if (!response.ok) {
    throw new Error(
      "Não foi possível carregar o Dashboard."
    );
  }

  return response.json();
}


const money = new Intl.NumberFormat(
  "pt-BR",
  {
    style: "currency",
    currency: "BRL",
  }
);


export default async function DashboardPage() {
  const summary =
    await getDashboardSummary();

  const maxStatus = Math.max(
    1,
    ...summary.por_status.map(
      (item) => item.total
    )
  );

  const maxRevenueProduct = Math.max(
    1,
    ...summary.por_produto.map(
      (item) => item.receita
    )
  );

  const maxRevenueOrigin = Math.max(
    1,
    ...summary.receita_por_origem.map(
      (item) => item.receita
    )
  );

  return (
    <div className="mx-auto max-w-7xl">

      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-cobalt-600">
          Business Intelligence
        </p>

        <h1 className="mt-1 text-3xl font-bold tracking-tight text-midnight">
          Dashboard comercial
        </h1>

        <p className="mt-2 text-slate-500">
          Indicadores calculados diretamente
          dos dados comerciais.
        </p>
      </header>


      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">

        <MetricCard
          title="Leads"
          value={String(
            summary.total_leads
          )}
          subtitle="Total cadastrado"
          icon={Users}
        />

        <MetricCard
          title="Ativos"
          value={String(
            summary.leads_ativos
          )}
          subtitle="Em processo comercial"
          icon={Activity}
        />

        <MetricCard
          title="Vendas"
          value={String(
            summary.vendas_pagas
          )}
          subtitle="Pagamentos confirmados"
          icon={ShoppingCart}
        />

        <MetricCard
          title="Conversão"
          value={`${summary.taxa_conversao.toFixed(
            2
          )}%`}
          subtitle="Leads convertidos"
          icon={Percent}
        />

        <MetricCard
          title="Receita"
          value={money.format(
            summary.receita_total
          )}
          subtitle="Receita confirmada"
          icon={Banknote}
        />

        <MetricCard
          title="Ticket médio"
          value={money.format(
            summary.ticket_medio
          )}
          subtitle="Valor médio por venda"
          icon={ReceiptText}
        />

        <MetricCard
          title="Contatos"
          value={String(
            summary.total_contatos
          )}
          subtitle="Contatos comerciais"
          icon={PhoneCall}
        />

        <MetricCard
          title="Interações"
          value={String(
            summary.total_interacoes
          )}
          subtitle="Histórico registrado"
          icon={MessageSquare}
        />

        <MetricCard
          title="Follow-ups"
          value={String(
            summary.followups_agendados
          )}
          subtitle="Retornos agendados"
          icon={CalendarClock}
        />

        <MetricCard
          title="Perdidos"
          value={String(
            summary.perdidos
          )}
          subtitle="Encerrados sem venda"
          icon={UserX}
        />

      </section>


      <section className="mt-6 grid gap-6 lg:grid-cols-2">

        <div className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-midnight">
            Funil comercial
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Distribuição atual dos Leads.
          </p>

          <div className="mt-6 space-y-5">

            {summary.por_status.map(
              (item) => {

                const width =
                  (item.total /
                    maxStatus) *
                  100;

                return (
                  <div key={item.status}>

                    <div className="mb-2 flex justify-between text-sm">
                      <span>
                        {item.status}
                      </span>

                      <strong>
                        {item.total}
                      </strong>
                    </div>

                    <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-cobalt-500"
                        style={{
                          width:
                            item.total === 0
                              ? "0%"
                              : `${width}%`,
                        }}
                      />
                    </div>

                  </div>
                );
              }
            )}

          </div>

        </div>


        <div className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-midnight">
            Conversão por origem
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Eficiência comercial de cada canal.
          </p>

          <div className="mt-6 space-y-4">

            {summary.conversao_por_origem.map(
              (item) => (
                <div
                  key={item.origem}
                  className="rounded-xl bg-ice p-4"
                >
                  <div className="flex justify-between">

                    <strong>
                      {item.origem}
                    </strong>

                    <strong className="text-cobalt-600">
                      {item.conversao.toFixed(
                        2
                      )}%
                    </strong>

                  </div>

                  <p className="mt-2 text-xs text-slate-500">
                    {item.convertidos} fechados
                    de {item.leads} Leads
                  </p>

                </div>
              )
            )}

          </div>

        </div>

      </section>


      <section className="mt-6 grid gap-6 lg:grid-cols-2">

        <div className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-midnight">
            Receita por produto
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Produtos que mais geram receita.
          </p>

          <div className="mt-6 space-y-5">

            {summary.por_produto.length === 0 ? (

              <p className="text-sm text-slate-500">
                Nenhuma venda registrada.
              </p>

            ) : (

              summary.por_produto.map(
                (item) => {

                  const width =
                    (item.receita /
                      maxRevenueProduct) *
                    100;

                  return (
                    <div
                      key={item.product_id}
                    >
                      <div className="mb-2 flex justify-between gap-4">

                        <div>
                          <p className="text-sm font-semibold text-slate-800">
                            {item.produto}
                          </p>

                          <p className="text-xs text-slate-400">
                            {item.vendas} venda(s)
                          </p>
                        </div>

                        <strong>
                          {money.format(
                            item.receita
                          )}
                        </strong>

                      </div>

                      <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-blue-500"
                          style={{
                            width:
                              `${width}%`,
                          }}
                        />
                      </div>

                    </div>
                  );
                }
              )

            )}

          </div>

        </div>


        <div className="rounded-card border border-slate-200 bg-white p-6 shadow-sm">

          <h2 className="text-lg font-bold text-midnight">
            Receita por origem
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Quanto cada canal trouxe em vendas.
          </p>

          <div className="mt-6 space-y-5">

            {summary.receita_por_origem.length === 0 ? (

              <p className="text-sm text-slate-500">
                Nenhuma receita registrada.
              </p>

            ) : (

              summary.receita_por_origem.map(
                (item) => {

                  const width =
                    (item.receita /
                      maxRevenueOrigin) *
                    100;

                  return (
                    <div
                      key={item.origem}
                    >
                      <div className="mb-2 flex justify-between">

                        <span className="text-sm font-semibold">
                          {item.origem}
                        </span>

                        <strong>
                          {money.format(
                            item.receita
                          )}
                        </strong>

                      </div>

                      <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-violet-500"
                          style={{
                            width:
                              `${width}%`,
                          }}
                        />
                      </div>

                    </div>
                  );
                }
              )

            )}

          </div>

        </div>

      </section>

    </div>
  );
}