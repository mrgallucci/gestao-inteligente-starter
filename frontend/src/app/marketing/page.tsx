import CampaignForm from "@/components/campaign-form";
type MarketingItem = {
  campaign_id: number;
  campanha: string;
  canal: string;
  custo: number;
  leads: number;
  convertidos: number;
  vendas: number;
  receita: number;
  conversao: number;
  cpl: number;
  cac: number | null;
  roi: number | null;
};

import { protectedJson } from "@/lib/server-protected";


async function getMarketing(): Promise<MarketingItem[]> {
  return protectedJson<MarketingItem[]>("/api/marketing-analytics", "Não foi possível carregar o Marketing Analytics.");
}


const money = new Intl.NumberFormat(
  "pt-BR",
  {
    style: "currency",
    currency: "BRL",
  }
);


export default async function MarketingPage() {
  const campaigns = await getMarketing();

  const custoTotal = campaigns.reduce(
    (total, item) =>
      total + item.custo,
    0
  );

  const receitaTotal = campaigns.reduce(
    (total, item) =>
      total + item.receita,
    0
  );

  const leadsTotal = campaigns.reduce(
    (total, item) =>
      total + item.leads,
    0
  );

  return (
    <div className="mx-auto max-w-7xl">

      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Marketing Analytics
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-950">
          Campanhas
        </h1>

        <p className="mt-2 text-slate-500">
          Acompanhe custo, aquisição,
          conversão e retorno das campanhas.
        </p>
      </header>


      <CampaignForm />

      <section className="mb-6 grid gap-4 sm:grid-cols-3">

        <Metric
          title="Investimento"
          value={money.format(custoTotal)}
        />

        <Metric
          title="Leads gerados"
          value={String(leadsTotal)}
        />

        <Metric
          title="Receita atribuída"
          value={money.format(receitaTotal)}
        />

      </section>


      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

        <div className="overflow-x-auto">

          <table className="w-full min-w-[1100px] text-left text-sm">

            <thead className="bg-slate-50 text-xs uppercase text-slate-500">
              <tr>

                <th className="px-5 py-4">
                  Campanha
                </th>

                <th className="px-5 py-4">
                  Canal
                </th>

                <th className="px-5 py-4">
                  Custo
                </th>

                <th className="px-5 py-4">
                  Leads
                </th>

                <th className="px-5 py-4">
                  Conversão
                </th>

                <th className="px-5 py-4">
                  CPL
                </th>

                <th className="px-5 py-4">
                  CAC
                </th>

                <th className="px-5 py-4">
                  Receita
                </th>

                <th className="px-5 py-4">
                  ROI
                </th>

              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">

              {campaigns.map(
                (campaign) => (

                  <tr key={campaign.campaign_id}>

                    <td className="px-5 py-4 font-semibold text-slate-900">
                      {campaign.campanha}
                    </td>

                    <td className="px-5 py-4">
                      {campaign.canal}
                    </td>

                    <td className="px-5 py-4">
                      {money.format(
                        campaign.custo
                      )}
                    </td>

                    <td className="px-5 py-4">
                      {campaign.leads}
                    </td>

                    <td className="px-5 py-4 font-semibold">
                      {campaign.conversao.toFixed(
                        2
                      )}%
                    </td>

                    <td className="px-5 py-4">
                      {money.format(
                        campaign.cpl
                      )}
                    </td>

                    <td className="px-5 py-4">
                      {campaign.cac === null
                        ? "—"
                        : money.format(
                            campaign.cac
                          )}
                    </td>

                    <td className="px-5 py-4 font-bold">
                      {money.format(
                        campaign.receita
                      )}
                    </td>

                    <td className="px-5 py-4">

                      {campaign.roi === null ? (
                        "—"
                      ) : (
                        <span
                          className={
                            campaign.roi >= 0
                              ? "font-bold text-emerald-600"
                              : "font-bold text-red-600"
                          }
                        >
                          {campaign.roi.toFixed(
                            2
                          )}%
                        </span>
                      )}

                    </td>

                  </tr>
                )
              )}

            </tbody>

          </table>

        </div>

      </section>


      {campaigns.length === 0 && (
        <div className="mt-6 rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-500">
          Nenhuma campanha cadastrada.
        </div>
      )}

    </div>
  );
}


function Metric({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

      <p className="text-sm text-slate-500">
        {title}
      </p>

      <p className="mt-2 text-3xl font-bold text-slate-950">
        {value}
      </p>

    </div>
  );
}