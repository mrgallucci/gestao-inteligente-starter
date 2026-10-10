"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  KeyRound,
  Pencil,
  ShieldCheck,
  UserCheck,
  UserPlus,
  UserX,
  X,
} from "lucide-react";

import {
  useRouter,
} from "next/navigation";

import { clientApi } from "@/lib/client-api";


type UserItem = {
  id: number;
  nome: string;
  email: string;
  role: string;

  lead_id:
    number | null;

  lead_nome:
    string | null;

  ativo: boolean;

  ultimo_login_em:
    string | null;

  criado_em:
    string;
};


type LeadOption = {
  id: number;
  nome: string;
  status: string;

  user_id:
    number | null;

  user_email:
    string | null;
};


function roleLabel(
  role: string
) {
  switch (role) {
    case "admin":
      return "Administrador";

    case "vendedor":
      return "Vendedor";

    case "aluno":
      return "Aluno";

    default:
      return role;
  }
}


type LoadResult =
  | { kind: "unauthorized" }
  | { kind: "forbidden" }
  | { kind: "failed" }
  | { kind: "network-error" }
  | { kind: "ok"; users: UserItem[]; leads: LeadOption[] };


async function fetchUsersAndLeads(): Promise<LoadResult> {
  try {
    const [
      usersResponse,
      leadsResponse,
    ] = await Promise.all([
      clientApi("/api/users"),
      clientApi("/api/admin/lead-options"),
    ]);

    if (
      usersResponse.status === 401 ||
      leadsResponse.status === 401
    ) {
      return { kind: "unauthorized" };
    }

    if (
      usersResponse.status === 403 ||
      leadsResponse.status === 403
    ) {
      return { kind: "forbidden" };
    }

    if (
      !usersResponse.ok ||
      !leadsResponse.ok
    ) {
      return { kind: "failed" };
    }

    return {
      kind: "ok",
      users: await usersResponse.json(),
      leads: await leadsResponse.json(),
    };
  } catch {
    return { kind: "network-error" };
  }
}


export default function UsersPage() {
  const router = useRouter();

  const [
    users,
    setUsers,
  ] = useState<UserItem[]>([]);

  const [
    leads,
    setLeads,
  ] = useState<LeadOption[]>([]);

  const [
    editingId,
    setEditingId,
  ] = useState<number | null>(
    null
  );

  const [nome, setNome] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [senha, setSenha] =
    useState("");

  const [role, setRole] =
    useState("vendedor");

  const [leadId, setLeadId] =
    useState("");

  const [ativo, setAtivo] =
    useState(true);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    saving,
    setSaving,
  ] = useState(false);

  const [
    message,
    setMessage,
  ] = useState("");

  const [
    error,
    setError,
  ] = useState("");


  // Busca sem alterar estado React: devolve o resultado e quem chama decide o
  // que fazer. Assim o effect inicial usa .then (sem setState síncrono no effect)
  // e os handlers continuam usando loadData() com o mesmo comportamento de antes.
  const applyLoadResult =
    useCallback(
      (result: LoadResult) => {
        switch (result.kind) {
          case "unauthorized":
            router.replace(
              "/login"
            );
            break;

          case "forbidden":
            setError(
              "Somente administradores podem acessar esta página."
            );
            break;

          case "failed":
            setError(
              "Não foi possível carregar os usuários."
            );
            break;

          case "network-error":
            setError(
              "Não foi possível conectar ao servidor."
            );
            break;

          case "ok":
            setUsers(
              result.users
            );

            setLeads(
              result.leads
            );
            break;
        }

        setLoading(false);
      },
      [router]
    );


  const loadData =
    useCallback(
      async () => {
        applyLoadResult(
          await fetchUsersAndLeads()
        );
      },
      [applyLoadResult]
    );


  useEffect(() => {
    let active = true;

    fetchUsersAndLeads().then(
      (result) => {
        if (active) {
          applyLoadResult(
            result
          );
        }
      }
    );

    return () => {
      active = false;
    };
  }, [applyLoadResult]);


  function resetForm() {
    setEditingId(null);
    setNome("");
    setEmail("");
    setSenha("");
    setRole("vendedor");
    setLeadId("");
    setAtivo(true);
    setMessage("");
    setError("");
  }


  function editUser(
    user: UserItem
  ) {
    setEditingId(
      user.id
    );

    setNome(
      user.nome
    );

    setEmail(
      user.email
    );

    setSenha("");

    setRole(
      user.role
    );

    setLeadId(
      user.lead_id !== null
        ? String(
            user.lead_id
          )
        : ""
    );

    setAtivo(
      user.ativo
    );

    setMessage("");
    setError("");

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

    setSaving(true);
    setMessage("");
    setError("");


    const payload = {
      nome,
      email,

      role,

      lead_id:
        role === "aluno"
          && leadId !== ""
          ? Number(leadId)
          : null,

      ativo,

      ...(editingId === null
        ? {
            senha,
          }
        : {
            senha:
              senha.trim() !== ""
                ? senha
                : null,
          }),
    };


    try {
      const response =
        await clientApi(
          editingId === null
            ? "/api/users"
            : `/api/users/${editingId}`,
          {
            method:
              editingId === null
                ? "POST"
                : "PUT",

            headers: {
              "Content-Type": "application/json",
            },

            body:
              JSON.stringify(
                payload
              ),
          }
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


      if (!response.ok) {
        setError(
          data.detail ??
            "Não foi possível salvar o usuário."
        );

        return;
      }


      setMessage(
        editingId === null
          ? "Usuário criado com sucesso!"
          : "Usuário atualizado com sucesso!"
      );


      setEditingId(null);
      setNome("");
      setEmail("");
      setSenha("");
      setRole("vendedor");
      setLeadId("");
      setAtivo(true);

      await loadData();

    } catch {
      setError(
        "Não foi possível conectar ao servidor."
      );

    } finally {
      setSaving(false);
    }
  }


  async function toggleUser(
    user: UserItem
  ) {

    const response =
      await clientApi(
        `/api/users/${user.id}`,
        {
          method: "PUT",

          headers: {
            "Content-Type": "application/json",
          },

          body:
            JSON.stringify({
              nome:
                user.nome,

              email:
                user.email,

              role:
                user.role,

              lead_id:
                user.lead_id,

              ativo:
                !user.ativo,

              senha:
                null,
            }),
        }
      );


    const data =
      await response.json();


    if (!response.ok) {
      setError(
        data.detail ??
          "Não foi possível alterar o usuário."
      );

      return;
    }


    setMessage(
      user.ativo
        ? "Usuário desativado."
        : "Usuário ativado."
    );

    await loadData();
  }


  if (loading) {
    return (
      <p className="text-slate-500">
        Carregando usuários...
      </p>
    );
  }


  return (
    <div className="mx-auto max-w-7xl">

      <header className="mb-8">

        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Administração
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-950">
          Gestão de Usuários
        </h1>

        <p className="mt-2 text-slate-500">
          Controle contas, perfis e
          permissões de acesso ao sistema.
        </p>

      </header>


      <form
        onSubmit={handleSubmit}
        className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
      >

        <div className="flex items-center justify-between gap-4">

          <div>

            <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
              {editingId
                ? "Editar usuário"
                : "Novo usuário"}
            </p>

            <h2 className="mt-1 text-xl font-bold">
              {editingId
                ? "Alterar conta"
                : "Criar conta"}
            </h2>

          </div>


          {editingId && (
            <button
              type="button"
              onClick={resetForm}
              className="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold"
            >
              <X size={16} />
              Cancelar
            </button>
          )}

        </div>


        <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          <div>

            <label className="mb-2 block text-sm font-medium">
              Nome
            </label>

            <input
              required
              value={nome}
              onChange={(event) =>
                setNome(
                  event.target.value
                )
              }
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium">
              E-mail
            </label>

            <input
              required
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              className="w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:border-emerald-500"
            />

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium">
              Perfil
            </label>

            <select
              value={role}
              onChange={(event) => {
                const value =
                  event.target.value;

                setRole(value);

                if (
                  value !==
                  "aluno"
                ) {
                  setLeadId("");
                }
              }}
              className="w-full rounded-xl border border-slate-200 px-4 py-3"
            >

              <option value="admin">
                Administrador
              </option>

              <option value="vendedor">
                Vendedor
              </option>

              <option value="aluno">
                Aluno
              </option>

            </select>

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium">
              {editingId
                ? "Nova senha"
                : "Senha"}
            </label>

            <input
              required={
                editingId === null
              }
              type="password"
              value={senha}
              onChange={(event) =>
                setSenha(
                  event.target.value
                )
              }
              placeholder={
                editingId
                  ? "Deixe vazio para manter"
                  : "Mínimo 8 caracteres"
              }
              className="w-full rounded-xl border border-slate-200 px-4 py-3"
            />

          </div>


          {role === "aluno" && (

            <div className="md:col-span-2">

              <label className="mb-2 block text-sm font-medium">
                Cliente / Lead associado
              </label>

              <select
                required
                value={leadId}
                onChange={(event) =>
                  setLeadId(
                    event.target.value
                  )
                }
                className="w-full rounded-xl border border-slate-200 px-4 py-3"
              >

                <option value="">
                  Selecione o cliente
                </option>


                {leads.map(
                  (lead) => {

                    const unavailable =
                      lead.user_id !==
                        null &&
                      lead.user_id !==
                        editingId;

                    return (
                      <option
                        key={lead.id}
                        value={lead.id}
                        disabled={
                          unavailable
                        }
                      >
                        {lead.nome}

                        {unavailable
                          ? ` — já possui usuário`
                          : ""}
                      </option>
                    );
                  }
                )}

              </select>

            </div>

          )}


          <div className="flex items-end">

            <label className="flex items-center gap-2 pb-3 text-sm font-medium">

              <input
                type="checkbox"
                checked={ativo}
                onChange={(event) =>
                  setAtivo(
                    event.target.checked
                  )
                }
              />

              Usuário ativo

            </label>

          </div>

        </div>


        {error && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}


        {message && (
          <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
            {message}
          </div>
        )}


        <button
          type="submit"
          disabled={saving}
          className="mt-6 flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 text-sm font-bold text-slate-950 disabled:opacity-50"
        >

          {editingId ? (
            <Pencil size={17} />
          ) : (
            <UserPlus size={17} />
          )}

          {saving
            ? "Salvando..."
            : editingId
            ? "Salvar alterações"
            : "Criar usuário"}

        </button>

      </form>


      <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

        <div className="border-b border-slate-200 p-6">

          <h2 className="text-lg font-bold">
            Usuários cadastrados
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {users.length} conta(s)
            cadastradas.
          </p>

        </div>


        <div className="overflow-x-auto">

          <table className="w-full min-w-[1000px] text-left text-sm">

            <thead className="bg-slate-50 text-xs uppercase text-slate-500">

              <tr>
                <th className="px-5 py-4">
                  Usuário
                </th>

                <th className="px-5 py-4">
                  Perfil
                </th>

                <th className="px-5 py-4">
                  Lead
                </th>

                <th className="px-5 py-4">
                  Status
                </th>

                <th className="px-5 py-4">
                  Último login
                </th>

                <th className="px-5 py-4">
                  Ações
                </th>
              </tr>

            </thead>


            <tbody className="divide-y divide-slate-100">

              {users.map(
                (user) => (

                  <tr key={user.id}>

                    <td className="px-5 py-4">

                      <p className="font-semibold">
                        {user.nome}
                      </p>

                      <p className="text-xs text-slate-500">
                        {user.email}
                      </p>

                    </td>


                    <td className="px-5 py-4">

                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold">

                        {user.role ===
                        "admin" ? (
                          <ShieldCheck
                            size={14}
                          />
                        ) : user.role ===
                          "aluno" ? (
                          <KeyRound
                            size={14}
                          />
                        ) : (
                          <UserCheck
                            size={14}
                          />
                        )}

                        {roleLabel(
                          user.role
                        )}

                      </span>

                    </td>


                    <td className="px-5 py-4">
                      {user.lead_nome ??
                        "—"}
                    </td>


                    <td className="px-5 py-4">

                      <span
                        className={
                          user.ativo
                            ? "font-semibold text-emerald-600"
                            : "font-semibold text-red-600"
                        }
                      >
                        {user.ativo
                          ? "Ativo"
                          : "Inativo"}
                      </span>

                    </td>


                    <td className="px-5 py-4">

                      {user.ultimo_login_em
                        ? new Date(
                            user.ultimo_login_em
                          ).toLocaleString(
                            "pt-BR"
                          )
                        : "Nunca"}

                    </td>


                    <td className="px-5 py-4">

                      <div className="flex gap-2">

                        <button
                          type="button"
                          onClick={() =>
                            editUser(
                              user
                            )
                          }
                          className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold"
                        >
                          <Pencil
                            size={14}
                          />

                          Editar
                        </button>


                        <button
                          type="button"
                          onClick={() =>
                            toggleUser(
                              user
                            )
                          }
                          className={
                            user.ativo
                              ? "flex items-center gap-1 rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-600"
                              : "flex items-center gap-1 rounded-lg border border-emerald-200 px-3 py-2 text-xs font-semibold text-emerald-600"
                          }
                        >

                          {user.ativo ? (
                            <UserX
                              size={14}
                            />
                          ) : (
                            <UserCheck
                              size={14}
                            />
                          )}

                          {user.ativo
                            ? "Desativar"
                            : "Ativar"}

                        </button>

                      </div>

                    </td>

                  </tr>
                )
              )}

            </tbody>

          </table>

        </div>

      </section>

    </div>
  );
}