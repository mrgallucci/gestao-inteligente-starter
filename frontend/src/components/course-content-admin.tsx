"use client";

import {
  BookOpen,
  CirclePlay,
  FileText,
  Pencil,
  Plus,
  Trash2,
  Upload,
  X,
} from "lucide-react";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import { clientApi } from "@/lib/client-api";

import {
  useAuth,
} from "@/components/auth-provider";

import {
  getHomeForRole,
} from "@/lib/permissions";


type Course = {
  id: number;
  nome: string;
  produto: string;
  ativo: boolean;
};


type CourseContent = {
  id: number;
  course_id: number;
  titulo: string;
  tipo: string;
  ordem: number;
  duracao_minutos: number | null;
  descricao: string | null;
  url_conteudo: string | null;
  ativo: boolean;
};


type Props = {
  courses: Course[];
};


export default function CourseContentAdmin({
  courses,
}: Props) {
  const router =
    useRouter();

  const {
    user,
    logout,
  } = useAuth();


  const [
    selectedCourseId,
    setSelectedCourseId,
  ] = useState(
    courses.length > 0
      ? String(
          courses[0].id
        )
      : ""
  );


  const [
    loadedContents,
    setContents,
  ] = useState<CourseContent[]>(
    []
  );

  // Sem curso selecionado não há conteúdos para mostrar. Derivado no render
  // (em vez de setContents([]) dentro de um effect).
  const contents =
    selectedCourseId
      ? loadedContents
      : [];


  const [
    editingId,
    setEditingId,
  ] = useState<number | null>(
    null
  );


  const [
    titulo,
    setTitulo,
  ] = useState("");


  const [
    tipo,
    setTipo,
  ] = useState(
    "video"
  );


  const [
    ordem,
    setOrdem,
  ] = useState(
    "1"
  );


  const [
    duracaoMinutos,
    setDuracaoMinutos,
  ] = useState("");


  const [
    descricao,
    setDescricao,
  ] = useState("");


  const [
    urlConteudo,
    setUrlConteudo,
  ] = useState("");


  const [
    ativo,
    setAtivo,
  ] = useState(
    true
  );


  const [
    salvando,
    setSalvando,
  ] = useState(
    false
  );


  const [
    mensagem,
    setMensagem,
  ] = useState("");


  const [
    enviandoArquivo,
    setEnviandoArquivo,
  ] = useState(false);


  const handleUnauthorized =
    useCallback(
      async () => {
        try {
          await fetch(
            "/api/session/logout",
            {
              method: "POST",
            }
          );
        } catch {
          // Mesmo se a rota de logout
          // falhar, limpamos a sessão local.
        }

        logout();

        router.replace(
          "/login"
        );

        router.refresh();
      },
      [logout, router]
    );


  const handleForbidden =
    useCallback(
      () => {
        setMensagem(
          "Seu perfil não possui permissão para administrar cursos."
        );

        if (user) {
          router.replace(
            getHomeForRole(
              user.role
            )
          );
        }
      },
      [router, user]
    );


  const loadContents =
    useCallback(
      async (
        courseId: number
      ) => {
        try {
          const response =
            await clientApi(
              `/api/courses/${courseId}/contents`
            );


          if (
            response.status === 401
          ) {
            await handleUnauthorized();
            return;
          }


          if (
            response.status === 403
          ) {
            handleForbidden();
            return;
          }


          if (!response.ok) {
            setMensagem(
              "Não foi possível carregar os conteúdos."
            );

            return;
          }


          const data =
            await response.json();


          setContents(
            data
          );

        } catch {
          setMensagem(
            "Não foi possível conectar ao servidor."
          );
        }
      },
      [
        handleForbidden,
        handleUnauthorized,
      ]
    );


  useEffect(() => {
    if (!selectedCourseId) {
      return;
    }

    let cancelled = false;

    clientApi(
      `/api/courses/${Number(selectedCourseId)}/contents`
    )
      .then(async (response) => {
        if (cancelled) {
          return;
        }

        if (response.status === 401) {
          await handleUnauthorized();
          return;
        }

        if (response.status === 403) {
          handleForbidden();
          return;
        }

        if (!response.ok) {
          setMensagem(
            "Não foi possível carregar os conteúdos."
          );
          return;
        }

        const data = await response.json();

        if (!cancelled) {
          setContents(data);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMensagem(
            "Não foi possível conectar ao servidor."
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    selectedCourseId,
    handleForbidden,
    handleUnauthorized,
  ]);


  function resetForm() {
    setEditingId(
      null
    );

    setTitulo("");

    setTipo(
      "video"
    );

    setOrdem(
      String(
        contents.length + 1
      )
    );

    setDuracaoMinutos("");

    setDescricao("");

    setUrlConteudo("");

    setAtivo(
      true
    );
  }


  function startEditing(
    content: CourseContent
  ) {
    setEditingId(
      content.id
    );


    setTitulo(
      content.titulo
    );


    setTipo(
      content.tipo
    );


    setOrdem(
      String(
        content.ordem
      )
    );


    setDuracaoMinutos(
      content.duracao_minutos !==
        null
        ? String(
            content.duracao_minutos
          )
        : ""
    );


    setDescricao(
      content.descricao ??
        ""
    );


    setUrlConteudo(
      content.url_conteudo ??
        ""
    );


    setAtivo(
      content.ativo
    );


    setMensagem("");


    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }


  async function handleSubmit(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();


    if (!selectedCourseId) {
      setMensagem(
        "Selecione um curso."
      );

      return;
    }


    setSalvando(
      true
    );

    setMensagem("");


    const payload = {
      titulo,
      tipo,

      ordem:
        Number(ordem),

      duracao_minutos:
        duracaoMinutos !== ""
          ? Number(
              duracaoMinutos
            )
          : null,

      descricao:
        descricao !== ""
          ? descricao
          : null,

      url_conteudo:
        urlConteudo !== ""
          ? urlConteudo
          : null,

      ativo,
    };


    const url =
      editingId !== null
        ? `/api/course-contents/${editingId}`
        : `/api/courses/${selectedCourseId}/contents`;


    const method =
      editingId !== null
        ? "PUT"
        : "POST";


    try {
      const response =
        await clientApi(
          url,
          {
            method,

            headers: {
              "Content-Type": "application/json",
            },

            body:
              JSON.stringify(
                payload
              ),
          }
        );


      if (
        response.status === 401
      ) {
        await handleUnauthorized();
        return;
      }


      if (
        response.status === 403
      ) {
        handleForbidden();
        return;
      }


      if (!response.ok) {
        const error =
          await response.json();


        setMensagem(
          error.detail ??
            "Não foi possível salvar."
        );

        return;
      }


      setMensagem(
        editingId !== null
          ? "Conteúdo atualizado com sucesso!"
          : "Conteúdo criado com sucesso!"
      );


      await loadContents(
        Number(
          selectedCourseId
        )
      );


      setEditingId(
        null
      );

      setTitulo("");

      setTipo(
        "video"
      );

      setOrdem(
        String(
          contents.length + 2
        )
      );

      setDuracaoMinutos("");

      setDescricao("");

      setUrlConteudo("");

      setAtivo(
        true
      );

    } catch {
      setMensagem(
        "Não foi possível conectar ao servidor."
      );

    } finally {
      setSalvando(
        false
      );
    }
  }


  async function uploadFile(file: File) {
    setEnviandoArquivo(true);
    setMensagem("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await clientApi(
        "/api/course-contents/upload",
        { method: "POST", body: formData }
      );

      if (response.status === 401) {
        await handleUnauthorized();
        return;
      }

      if (response.status === 403) {
        handleForbidden();
        return;
      }

      const data = await response.json();
      if (!response.ok) {
        setMensagem(data.detail ?? "Não foi possível enviar o arquivo.");
        return;
      }

      setUrlConteudo(data.url);
      setMensagem("Arquivo enviado. A URL foi vinculada ao conteúdo.");
    } catch {
      setMensagem("Não foi possível enviar o arquivo.");
    } finally {
      setEnviandoArquivo(false);
    }
  }


  async function deleteContent(
    content: CourseContent
  ) {
    const confirmed =
      window.confirm(
        `Desativar "${content.titulo}"? O histórico de progresso será preservado.`
      );


    if (!confirmed) {
      return;
    }


    setMensagem("");


    try {
      const response =
        await clientApi(
          `/api/course-contents/${content.id}`,
          { method: "DELETE" }
        );


      if (
        response.status === 401
      ) {
        await handleUnauthorized();
        return;
      }


      if (
        response.status === 403
      ) {
        handleForbidden();
        return;
      }


      if (!response.ok) {
        const error =
          await response
            .json()
            .catch(
              () => null
            );


        setMensagem(
          error?.detail ??
            "Não foi possível desativar o conteúdo."
        );

        return;
      }


      if (
        editingId ===
        content.id
      ) {
        resetForm();
      }


      setMensagem(
        "Conteúdo desativado com sucesso."
      );


      await loadContents(
        Number(
          selectedCourseId
        )
      );

    } catch {
      setMensagem(
        "Não foi possível conectar ao servidor."
      );
    }
  }


  const selectedCourse =
    courses.find(
      (course) =>
        course.id ===
        Number(
          selectedCourseId
        )
    );


  return (
    <div>

      {/* SELEÇÃO DO CURSO */}
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="grid gap-5 lg:grid-cols-[1fr_2fr]">

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">
              Curso
            </label>


            <select
              value={
                selectedCourseId
              }
              onChange={(
                event
              ) => {
                setSelectedCourseId(
                  event.target.value
                );

                resetForm();
              }}
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            >

              {courses.map(
                (course) => (

                  <option
                    key={
                      course.id
                    }
                    value={
                      course.id
                    }
                  >
                    {course.nome}
                  </option>

                )
              )}

            </select>

          </div>


          {selectedCourse && (

            <div className="rounded-xl bg-slate-50 p-4">

              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Produto relacionado
              </p>

              <p className="mt-1 font-semibold text-slate-900">
                {
                  selectedCourse.produto
                }
              </p>

            </div>

          )}

        </div>

      </section>


      {/* FORMULÁRIO */}
      <form
        onSubmit={
          handleSubmit
        }
        className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >

        <div className="flex items-center justify-between gap-4">

          <div>

            <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
              {editingId
                ? "Editar conteúdo"
                : "Novo conteúdo"}
            </p>

            <h2 className="mt-1 text-xl font-bold text-slate-950">
              {editingId
                ? "Alterar material"
                : "Adicionar ao curso"}
            </h2>

          </div>


          {editingId && (

            <button
              type="button"
              onClick={
                resetForm
              }
              className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold"
            >
              <X size={17} />

              Cancelar edição
            </button>

          )}

        </div>


        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          <div className="xl:col-span-2">

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Título
            </label>

            <input
              required
              value={
                titulo
              }
              onChange={(
                event
              ) =>
                setTitulo(
                  event.target.value
                )
              }
              placeholder="Ex.: Vídeo 2 - Planejamento do Jardim"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Tipo
            </label>

            <select
              value={
                tipo
              }
              onChange={(
                event
              ) =>
                setTipo(
                  event.target.value
                )
              }
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            >

              <option value="video">
                Vídeo
              </option>

              <option value="apostila">
                Apostila
              </option>

              <option value="material">
                Material
              </option>

            </select>

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Ordem
            </label>

            <input
              required
              type="number"
              min="1"
              value={
                ordem
              }
              onChange={(
                event
              ) =>
                setOrdem(
                  event.target.value
                )
              }
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Duração em minutos
            </label>

            <input
              type="number"
              min="0"
              value={
                duracaoMinutos
              }
              onChange={(
                event
              ) =>
                setDuracaoMinutos(
                  event.target.value
                )
              }
              placeholder="Ex.: 15"
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>


          <div className="md:col-span-2 xl:col-span-3">

            <label className="mb-2 block text-sm font-medium text-slate-700">
              URL do conteúdo
            </label>

            <input
              type="url"
              value={
                urlConteudo
              }
              onChange={(
                event
              ) =>
                setUrlConteudo(
                  event.target.value
                )
              }
              placeholder="https://..."
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>


          <div className="md:col-span-2 xl:col-span-4">
            <label className="mb-2 block text-sm font-medium text-slate-700">
              Upload local (opcional)
            </label>
            <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600 hover:border-emerald-400">
              <Upload size={18} />
              {enviandoArquivo ? "Enviando arquivo..." : "Selecionar arquivo (até 50 MB)"}
              <input
                type="file"
                disabled={enviandoArquivo}
                accept=".pdf,.mp4,.webm,.mov,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg"
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) uploadFile(file);
                  event.currentTarget.value = "";
                }}
              />
            </label>
            <p className="mt-2 text-xs text-slate-400">Ao enviar, a URL local é preenchida automaticamente. Em produção, substitua por Supabase Storage/S3.</p>
          </div>


          <div className="md:col-span-2 xl:col-span-4">

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Descrição
            </label>

            <textarea
              value={
                descricao
              }
              onChange={(
                event
              ) =>
                setDescricao(
                  event.target.value
                )
              }
              rows={3}
              placeholder="Descrição do conteúdo..."
              className="w-full resize-none rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>

        </div>


        <div className="mt-5 flex flex-wrap items-center gap-4">

          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">

            <input
              type="checkbox"
              checked={
                ativo
              }
              onChange={(
                event
              ) =>
                setAtivo(
                  event.target.checked
                )
              }
            />

            Conteúdo ativo

          </label>


          <button
            type="submit"
            disabled={
              salvando ||
              !selectedCourseId
            }
            className="flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-50"
          >

            {editingId ? (
              <Pencil
                size={18}
              />
            ) : (
              <Plus
                size={18}
              />
            )}


            {salvando
              ? "Salvando..."
              : editingId
              ? "Salvar alterações"
              : "Adicionar conteúdo"}

          </button>


          {mensagem && (

            <p className="text-sm text-slate-600">
              {mensagem}
            </p>

          )}

        </div>

      </form>


      {/* LISTAGEM */}
      <section className="mt-6">

        <div className="mb-4">

          <h2 className="text-xl font-bold text-slate-950">
            Conteúdo do curso
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {contents.length} item(ns)
            cadastrados.
          </p>

        </div>


        <div className="space-y-3">

          {contents.map(
            (content) => (

              <div
                key={
                  content.id
                }
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >

                <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

                  <div className="flex gap-4">

                    <div className="rounded-xl bg-slate-100 p-3">

                      {content.tipo ===
                      "video" ? (

                        <CirclePlay
                          size={23}
                        />

                      ) : content.tipo ===
                        "apostila" ? (

                        <BookOpen
                          size={23}
                        />

                      ) : (

                        <FileText
                          size={23}
                        />

                      )}

                    </div>


                    <div>

                      <div className="flex flex-wrap items-center gap-2">

                        <span className="text-xs font-semibold uppercase text-slate-400">
                          {
                            content.tipo
                          }
                        </span>


                        {!content.ativo && (

                          <span className="rounded-full bg-red-50 px-2 py-1 text-xs font-semibold text-red-600">
                            Inativo
                          </span>

                        )}

                      </div>


                      <h3 className="mt-1 font-bold text-slate-950">
                        {content.ordem}.{" "}
                        {content.titulo}
                      </h3>


                      {content.duracao_minutos !==
                        null && (

                        <p className="mt-1 text-xs text-slate-500">
                          {
                            content.duracao_minutos
                          }{" "}
                          minutos
                        </p>

                      )}


                      {content.descricao && (

                        <p className="mt-2 max-w-2xl text-sm text-slate-500">
                          {
                            content.descricao
                          }
                        </p>

                      )}


                      {content.url_conteudo && (

                        <a
                          href={
                            content.url_conteudo
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-2 inline-block text-sm font-semibold text-emerald-600 hover:underline"
                        >
                          Abrir conteúdo
                        </a>

                      )}

                    </div>

                  </div>


                  <div className="flex gap-2">

                    <button
                      type="button"
                      onClick={() =>
                        startEditing(
                          content
                        )
                      }
                      className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold hover:bg-slate-50"
                    >
                      <Pencil
                        size={16}
                      />

                      Editar
                    </button>


                    <button
                      type="button"
                      disabled={!content.ativo}
                      onClick={() =>
                        deleteContent(
                          content
                        )
                      }
                      className="flex items-center gap-2 rounded-xl border border-red-200 px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      <Trash2
                        size={16}
                      />

                      {content.ativo ? "Desativar" : "Desativado"}
                    </button>

                  </div>

                </div>

              </div>

            )
          )}

        </div>


        {contents.length === 0 && (

          <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
            Nenhum conteúdo cadastrado
            neste curso.
          </div>

        )}

      </section>

    </div>
  );
}