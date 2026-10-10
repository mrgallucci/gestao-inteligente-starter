import Link from "next/link";

import {
  redirect,
} from "next/navigation";

import {
  serverApi,
} from "@/lib/server-api";

import {
  getHomeForRole,
} from "@/lib/permissions";


type ContentAnalytics = {
  content_id: number;
  course_id: number;
  curso: string;
  titulo: string;
  tipo: string;
  ordem: number;
  matriculas: number;
  aberturas: number;
  conclusoes: number;
  taxa_abertura: number;
  progresso_medio: number;
};


type LMSAnalytics = {
  total_matriculas: number;
  acessos_liberados: number;
  primeiro_acesso: number;
  nunca_acessaram: number;
  em_andamento: number;
  concluidos: number;
  possivel_abandono: number;
  progresso_medio: number;
  taxa_primeiro_acesso: number;
  taxa_conclusao: number;
  por_conteudo: ContentAnalytics[];
};


type Enrollment = {
  id: number;
  lead_id: number;
  aluno: string;
  origem: string;
  course_id: number;
  curso: string;
  status: string;
  progresso: number;
  acesso_liberado_em: string;
  primeiro_acesso_em: string | null;
  ultimo_acesso_em: string | null;
  concluido_em: string | null;
};


async function handleProtectedResponse(
  response: Response,
  errorMessage: string
) {
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
      errorMessage
    );
  }


  return response;
}


async function getLMSAnalytics():
  Promise<LMSAnalytics> {

  const response =
    await serverApi(
      "/api/lms-analytics"
    );


  await handleProtectedResponse(
    response,
    "Não foi possível carregar o LMS Analytics."
  );


  return response.json();
}


async function getEnrollments():
  Promise<Enrollment[]> {

  const response =
    await serverApi(
      "/api/enrollments"
    );


  await handleProtectedResponse(
    response,
    "Não foi possível carregar as matrículas."
  );


  return response.json();
}


export default async function LMSPage() {
  const [
    analytics,
    enrollments,
  ] = await Promise.all([
    getLMSAnalytics(),
    getEnrollments(),
  ]);


  return (
    <div className="mx-auto max-w-7xl">

      <header className="mb-8">

        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Learning Management System
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-950">
          LMS Analytics
        </h1>

        <p className="mt-2 text-slate-500">
          Acompanhe acesso, consumo,
          progresso e conclusão dos cursos.
        </p>

      </header>


      {/* MÉTRICAS */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <Metric
          title="Matrículas"
          value={
            analytics.total_matriculas
          }
          subtitle="Acessos liberados"
        />


        <Metric
          title="Primeiro acesso"
          value={
            analytics.primeiro_acesso
          }
          subtitle={`${analytics.taxa_primeiro_acesso.toFixed(
            2
          )}% das matrículas`}
        />


        <Metric
          title="Nunca acessaram"
          value={
            analytics.nunca_acessaram
          }
          subtitle="Compraram, mas não entraram"
        />


        <Metric
          title="Em andamento"
          value={
            analytics.em_andamento
          }
          subtitle="Alunos ativos"
        />


        <Metric
          title="Concluídos"
          value={
            analytics.concluidos
          }
          subtitle={`${analytics.taxa_conclusao.toFixed(
            2
          )}% de conclusão`}
        />


        <Metric
          title="Possível abandono"
          value={
            analytics.possivel_abandono
          }
          subtitle="7+ dias sem atividade"
        />


        <Metric
          title="Progresso médio"
          value={`${analytics.progresso_medio.toFixed(
            2
          )}%`}
          subtitle="Média geral dos alunos"
        />


        <Metric
          title="Acessos liberados"
          value={
            analytics.acessos_liberados
          }
          subtitle="Matrículas criadas"
        />

      </section>


      {/* DESEMPENHO POR CONTEÚDO */}
      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <h2 className="text-lg font-bold text-slate-950">
          Desempenho por conteúdo
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Veja onde os alunos entram,
          avançam ou deixam de continuar.
        </p>


        <div className="mt-6 overflow-x-auto">

          <table className="w-full min-w-[900px] text-left text-sm">

            <thead className="border-b border-slate-200 text-xs uppercase text-slate-400">

              <tr>

                <th className="py-3">
                  Conteúdo
                </th>

                <th className="py-3">
                  Tipo
                </th>

                <th className="py-3">
                  Matrículas
                </th>

                <th className="py-3">
                  Aberturas
                </th>

                <th className="py-3">
                  Taxa abertura
                </th>

                <th className="py-3">
                  Conclusões
                </th>

                <th className="py-3">
                  Progresso médio
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-slate-100">

              {analytics.por_conteudo.map(
                (item) => (

                  <tr
                    key={
                      item.content_id
                    }
                  >

                    <td className="py-4">

                      <p className="font-semibold text-slate-900">
                        {item.titulo}
                      </p>

                      <p className="text-xs text-slate-400">
                        {item.curso}
                      </p>

                    </td>


                    <td className="py-4 capitalize">
                      {item.tipo}
                    </td>


                    <td className="py-4">
                      {item.matriculas}
                    </td>


                    <td className="py-4">
                      {item.aberturas}
                    </td>


                    <td className="py-4 font-semibold">
                      {item.taxa_abertura.toFixed(
                        2
                      )}%
                    </td>


                    <td className="py-4">
                      {item.conclusoes}
                    </td>


                    <td className="py-4">

                      <div className="w-40">

                        <div className="mb-1 flex justify-between text-xs">

                          <span>
                            Progresso
                          </span>

                          <span>
                            {item.progresso_medio.toFixed(
                              0
                            )}%
                          </span>

                        </div>


                        <div className="h-2 overflow-hidden rounded-full bg-slate-100">

                          <div
                            className="h-full rounded-full bg-emerald-500"
                            style={{
                              width:
                                `${Math.min(
                                  item.progresso_medio,
                                  100
                                )}%`,
                            }}
                          />

                        </div>

                      </div>

                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

        </div>


        {analytics.por_conteudo.length ===
          0 && (

          <p className="mt-6 text-sm text-slate-500">
            Nenhum conteúdo cadastrado ainda.
          </p>

        )}

      </section>


      {/* MATRÍCULAS */}
      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

        <div className="border-b border-slate-200 p-6">

          <h2 className="text-lg font-bold text-slate-950">
            Alunos e matrículas
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Situação individual de cada aluno.
          </p>

        </div>


        <div className="overflow-x-auto">

          <table className="w-full min-w-[1000px] text-left text-sm">

            <thead className="bg-slate-50 text-xs uppercase text-slate-500">

              <tr>

                <th className="px-5 py-4">
                  Aluno
                </th>

                <th className="px-5 py-4">
                  Curso
                </th>

                <th className="px-5 py-4">
                  Origem
                </th>

                <th className="px-5 py-4">
                  Status
                </th>

                <th className="px-5 py-4">
                  Progresso
                </th>

                <th className="px-5 py-4">
                  Primeiro acesso
                </th>

                <th className="px-5 py-4">
                  Área do aluno
                </th>

              </tr>

            </thead>


            <tbody className="divide-y divide-slate-100">

              {enrollments.map(
                (item) => (

                  <tr key={item.id}>

                    <td className="px-5 py-4 font-semibold">

                      <Link
                        href={`/leads/${item.lead_id}`}
                        className="hover:text-emerald-600"
                      >
                        {item.aluno}
                      </Link>

                    </td>


                    <td className="px-5 py-4">
                      {item.curso}
                    </td>


                    <td className="px-5 py-4">
                      {item.origem}
                    </td>


                    <td className="px-5 py-4">
                      {item.status}
                    </td>


                    <td className="px-5 py-4 font-semibold">
                      {item.progresso.toFixed(
                        2
                      )}%
                    </td>


                    <td className="px-5 py-4">

                      {item.primeiro_acesso_em
                        ? new Date(
                            item.primeiro_acesso_em
                          ).toLocaleString(
                            "pt-BR"
                          )
                        : "Nunca acessou"}

                    </td>


                    <td className="px-5 py-4">

                      <Link
                        href={`/aluno/${item.id}`}
                        className="font-semibold text-emerald-600 hover:underline"
                      >
                        Abrir curso
                      </Link>

                    </td>

                  </tr>

                )
              )}

            </tbody>

          </table>

        </div>


        {enrollments.length === 0 && (

          <div className="p-8 text-center text-sm text-slate-500">
            Nenhuma matrícula cadastrada.
          </div>

        )}

      </section>

    </div>
  );
}


function Metric({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: number | string;
  subtitle: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

      <p className="text-sm text-slate-500">
        {title}
      </p>

      <p className="mt-2 text-3xl font-bold text-slate-950">
        {value}
      </p>

      <p className="mt-2 text-xs text-slate-400">
        {subtitle}
      </p>

    </div>
  );
}