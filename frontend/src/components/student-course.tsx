"use client";

import {
  BookOpen,
  CheckCircle2,
  CirclePlay,
  ExternalLink,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import { clientApi } from "@/lib/client-api";


type Content = {
  id: number;
  titulo: string;
  tipo: string;
  ordem: number;

  duracao_minutos:
    number | null;

  descricao:
    string | null;

  url_conteudo:
    string | null;

  progresso: number;

  aberto_em:
    string | null;

  ultima_atividade_em:
    string | null;

  concluido_em:
    string | null;
};


type Enrollment = {
  id: number;
  lead_id: number;
  aluno: string;

  course_id: number;
  curso: string;

  descricao:
    string | null;

  status: string;
  progresso: number;

  acesso_liberado_em:
    string;

  primeiro_acesso_em:
    string | null;

  ultimo_acesso_em:
    string | null;

  concluido_em:
    string | null;

  conteudos: Content[];
};


type Props = {
  enrollment: Enrollment;
};


export default function StudentCourse({
  enrollment,
}: Props) {
  const router =
    useRouter();


  const [
    contents,
    setContents,
  ] = useState(
    enrollment.conteudos
  );


  const [
    courseProgress,
    setCourseProgress,
  ] = useState(
    enrollment.progresso
  );


  const [
    courseStatus,
    setCourseStatus,
  ] = useState(
    enrollment.status
  );


  const [
    selectedContent,
    setSelectedContent,
  ] = useState<
    number | null
  >(null);


  const [
    error,
    setError,
  ] = useState("");


  // =====================================================
  // PRIMEIRO ACESSO AO CURSO
  // =====================================================

  useEffect(() => {
    async function registerAccess() {
      try {
        const response =
          await clientApi(
            `/api/enrollments/${enrollment.id}/access`,
            { method: "POST" }
          );


        if (
          response.status === 401
        ) {
          router.replace(
            "/login"
          );

          return;
        }


        if (
          response.status === 403
        ) {
          const data =
            await response.json();

          setError(
            data.detail ??
              "Você não possui acesso a este curso."
          );

          return;
        }


        if (!response.ok) {
          setError(
            "Não foi possível registrar o acesso ao curso."
          );

          return;
        }


        if (
          courseStatus ===
          "Acesso liberado"
        ) {
          setCourseStatus(
            "Em andamento"
          );
        }

      } catch {
        setError(
          "Não foi possível conectar ao servidor."
        );
      }
    }


    registerAccess();

  }, [
    enrollment.id,
    courseStatus,
    router,
  ]);


  // =====================================================
  // ABRIR CONTEÚDO
  // =====================================================

  async function openContent(
    contentId: number
  ) {
    setError("");


    try {
      const response =
        await clientApi(
          `/api/enrollments/${enrollment.id}/contents/${contentId}/open`,
          { method: "POST" }
        );


      const data =
        await response.json();


      if (
        response.status === 401
      ) {
        router.replace(
          "/login"
        );

        return;
      }


      if (
        response.status === 403
      ) {
        setError(
          data.detail ??
            "Você não possui acesso a este conteúdo."
        );

        return;
      }


      if (!response.ok) {
        setError(
          data.detail ??
            "Não foi possível abrir o conteúdo."
        );

        return;
      }


      setSelectedContent(
        contentId
      );


      setContents(
        (current) =>
          current.map(
            (item) =>
              item.id === contentId
                ? {
                    ...item,

                    aberto_em:
                      item.aberto_em ??
                      new Date()
                        .toISOString(),

                    ultima_atividade_em:
                      new Date()
                        .toISOString(),
                  }
                : item
          )
      );


      if (
        courseStatus ===
        "Acesso liberado"
      ) {
        setCourseStatus(
          "Em andamento"
        );
      }

    } catch {
      setError(
        "Não foi possível conectar ao servidor."
      );
    }
  }


  // =====================================================
  // ATUALIZAR PROGRESSO
  // =====================================================

  async function updateProgress(
    contentId: number,
    progress: number
  ) {
    setError("");


    try {
      const response =
        await clientApi(
          `/api/enrollments/${enrollment.id}/contents/${contentId}/progress`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },

            body:
              JSON.stringify({
                progresso:
                  progress,
              }),
          }
        );


      const result =
        await response.json();


      if (
        response.status === 401
      ) {
        router.replace(
          "/login"
        );

        return;
      }


      if (
        response.status === 403
      ) {
        setError(
          result.detail ??
            "Você não possui permissão para atualizar este conteúdo."
        );

        return;
      }


      if (!response.ok) {
        setError(
          result.detail ??
            "Não foi possível atualizar o progresso."
        );

        return;
      }


      setContents(
        (current) =>
          current.map(
            (item) =>
              item.id === contentId
                ? {
                    ...item,

                    progresso:
                      result.progresso,

                    ultima_atividade_em:
                      new Date()
                        .toISOString(),

                    concluido_em:
                      result.progresso === 100
                        ? new Date()
                            .toISOString()
                        : null,
                  }
                : item
          )
      );


      setCourseProgress(
        result.progresso_curso
      );


      setCourseStatus(
        result.status_curso
      );

    } catch {
      setError(
        "Não foi possível conectar ao servidor."
      );
    }
  }


  // =====================================================
  // INTERFACE
  // =====================================================

  return (
    <div className="mx-auto max-w-6xl">

      {/* CABEÇALHO DO CURSO */}
      <header className="rounded-3xl bg-slate-950 p-8 text-white">

        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-400">
          Área do aluno
        </p>


        <h1 className="mt-2 text-3xl font-bold">
          {enrollment.curso}
        </h1>


        {enrollment.descricao && (
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
            {enrollment.descricao}
          </p>
        )}


        <p className="mt-6 text-sm text-slate-400">
          Aluno
        </p>

        <p className="text-lg font-semibold">
          {enrollment.aluno}
        </p>


        <div className="mt-8">

          <div className="mb-2 flex justify-between text-sm">

            <span>
              Progresso geral
            </span>

            <strong>
              {courseProgress.toFixed(
                0
              )}%
            </strong>

          </div>


          <div className="h-3 overflow-hidden rounded-full bg-slate-700">

            <div
              className="h-full rounded-full bg-emerald-400 transition-all duration-300"
              style={{
                width:
                  `${Math.min(
                    courseProgress,
                    100
                  )}%`,
              }}
            />

          </div>


          <p className="mt-3 text-sm text-slate-300">
            Status:{" "}

            <strong>
              {courseStatus}
            </strong>
          </p>

        </div>

      </header>


      {/* ERROS */}
      {error && (
        <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}


      {/* CONTEÚDOS */}
      <section className="mt-6">

        <h2 className="text-xl font-bold text-slate-950">
          Conteúdo do curso
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Selecione um conteúdo para
          continuar seus estudos.
        </p>


        <div className="mt-6 space-y-4">

          {contents.map(
            (content) => {

              const selected =
                selectedContent
                === content.id;

              const concluded =
                content.progresso
                === 100;


              return (
                <div
                  key={content.id}
                  className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
                >

                  {/* CABEÇALHO DO CONTEÚDO */}
                  <div className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">

                    <div className="flex items-start gap-4">

                      <div className="rounded-xl bg-slate-100 p-3">

                        {content.tipo ===
                        "video" ? (

                          <CirclePlay
                            size={24}
                          />

                        ) : (

                          <BookOpen
                            size={24}
                          />

                        )}

                      </div>


                      <div>

                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                          {content.tipo}
                        </p>


                        <h3 className="font-bold text-slate-900">
                          {content.ordem}.{" "}
                          {content.titulo}
                        </h3>


                        {content.duracao_minutos !==
                          null && (

                          <p className="mt-1 text-xs text-slate-500">
                            {
                              content
                                .duracao_minutos
                            }{" "}
                            minutos
                          </p>

                        )}

                      </div>

                    </div>


                    <div className="flex items-center gap-3">

                      {concluded && (

                        <CheckCircle2
                          className="text-emerald-500"
                          size={22}
                        />

                      )}


                      <button
                        type="button"
                        onClick={() =>
                          openContent(
                            content.id
                          )
                        }
                        className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700"
                      >
                        {content.aberto_em
                          ? "Abrir novamente"
                          : "Abrir conteúdo"}
                      </button>

                    </div>

                  </div>


                  {/* PROGRESSO INDIVIDUAL */}
                  <div className="border-t border-slate-100 px-5 py-4">

                    <div className="mb-2 flex justify-between text-xs text-slate-500">

                      <span>
                        Progresso
                      </span>

                      <strong>
                        {content.progresso}%
                      </strong>

                    </div>


                    <div className="h-2 overflow-hidden rounded-full bg-slate-100">

                      <div
                        className="h-full rounded-full bg-emerald-500 transition-all duration-300"
                        style={{
                          width:
                            `${Math.min(
                              content.progresso,
                              100
                            )}%`,
                        }}
                      />

                    </div>

                  </div>


                  {/* CONTEÚDO SELECIONADO */}
                  {selected && (

                    <div className="border-t border-slate-200 bg-slate-50 p-5">

                      <p className="font-semibold text-slate-900">
                        {content.titulo}
                      </p>


                      {content.descricao && (

                        <p className="mt-2 text-sm leading-6 text-slate-500">
                          {
                            content
                              .descricao
                          }
                        </p>

                      )}


                      {content.url_conteudo ? (

                        <a
                          href={
                            content
                              .url_conteudo
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                        >
                          <ExternalLink
                            size={16}
                          />

                          Abrir conteúdo real
                        </a>

                      ) : (

                        <p className="mt-3 text-sm text-amber-600">
                          Nenhum arquivo ou
                          vídeo foi vinculado
                          a este conteúdo ainda.
                        </p>

                      )}


                      {/* CONTROLE DE PROGRESSO */}
                      <div className="mt-6 border-t border-slate-200 pt-5">

                        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                          Progresso de teste
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Estes botões simulam
                          o consumo do conteúdo
                          enquanto ainda não
                          conectamos o player
                          ou arquivo automático.
                        </p>


                        <div className="mt-4 flex flex-wrap gap-2">

                          {[
                            25,
                            50,
                            75,
                            100,
                          ].map(
                            (progress) => (

                              <button
                                key={
                                  progress
                                }
                                type="button"
                                onClick={() =>
                                  updateProgress(
                                    content.id,
                                    progress
                                  )
                                }
                                className={
                                  progress === 100
                                    ? "rounded-lg bg-emerald-500 px-4 py-2 text-sm font-bold text-slate-950 transition hover:bg-emerald-400"
                                    : "rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
                                }
                              >
                                {progress ===
                                100
                                  ? "Concluir"
                                  : `${progress}%`}
                              </button>

                            )
                          )}

                        </div>

                      </div>

                    </div>

                  )}

                </div>
              );
            }
          )}

        </div>


        {contents.length === 0 && (

          <div className="mt-6 rounded-2xl border border-dashed border-slate-300 p-10 text-center">

            <BookOpen
              size={32}
              className="mx-auto text-slate-400"
            />

            <p className="mt-3 font-semibold text-slate-700">
              Nenhum conteúdo disponível.
            </p>

          </div>

        )}

      </section>

    </div>
  );
}