"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  BrainCircuit,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
} from "lucide-react";

import { useRouter } from "next/navigation";

import {
  useAuth,
} from "@/components/auth-provider";

import {
  getHomeForRole,
} from "@/lib/permissions";


type LoginResponse = {
  user: {
    id: number;
    nome: string;
    email: string;
    role: string;
    lead_id?: number | null;
    ativo?: boolean;
  };
};


export default function LoginPage() {
  const router = useRouter();

  const {
    user,
    loading,
    login,
  } = useAuth();


  const [email, setEmail] =
    useState("");

  const [senha, setSenha] =
    useState("");

  const [
    mostrarSenha,
    setMostrarSenha,
  ] = useState(false);

  const [
    carregando,
    setCarregando,
  ] = useState(false);

  const [erro, setErro] =
    useState("");


  // Se o usuário já estiver logado
  // e tentar abrir /login,
  // manda para a página correta
  // conforme o perfil.
  useEffect(() => {
    if (
      !loading &&
      user
    ) {
      router.replace(
        getHomeForRole(
          user.role
        )
      );
    }
  }, [
    loading,
    user,
    router,
  ]);


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setCarregando(true);
    setErro("");


    try {
      const response = await fetch(
         "/api/session/login",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            email,
            senha,
          }),
        }
      );


      const data =
        await response.json();


      if (!response.ok) {
        setErro(
          data.detail ??
            "Não foi possível entrar."
        );

        setCarregando(false);

        return;
      }


      const loginData =
        data as LoginResponse;


      // O JWT fica apenas no cookie HttpOnly.
      // O React mantém somente os dados não sensíveis do usuário.
      login({
        id: loginData.user.id,
        nome: loginData.user.nome,
        email: loginData.user.email,
        role: loginData.user.role,
        lead_id: loginData.user.lead_id ?? null,
        ativo: loginData.user.ativo ?? true,
      });


      // Cada perfil vai para
      // sua área correta.
      router.replace(
        getHomeForRole(
          loginData.user.role
        )
      );

      router.refresh();

    } catch {
      setErro(
        "Não foi possível conectar ao servidor."
      );

      setCarregando(false);
    }
  }


  return (
    <main className="flex min-h-screen bg-slate-950">

      {/* LADO ESQUERDO */}
      <section className="hidden w-1/2 flex-col justify-between p-12 lg:flex">

        <div className="flex items-center gap-3">

          <div className="rounded-2xl bg-emerald-400 p-3 text-slate-950">
            <BrainCircuit
              size={28}
            />
          </div>

          <div>

            <p className="font-bold text-white">
              Gestão Inteligente
            </p>

            <p className="text-xs text-slate-400">
              Commercial Intelligence
            </p>

          </div>

        </div>


        <div className="max-w-xl">

          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-emerald-400">
            Gestão orientada por dados
          </p>

          <h1 className="mt-5 text-5xl font-bold leading-tight text-white">
            Do primeiro contato ao
            comportamento pós-venda.
          </h1>

          <p className="mt-6 text-lg leading-8 text-slate-400">
            CRM, vendas, marketing,
            Customer Analytics e LMS
            conectados em uma única
            operação.
          </p>

        </div>


        <p className="text-xs text-slate-600">
          Gestão Inteligente
        </p>

      </section>


      {/* LADO DIREITO */}
      <section className="flex w-full items-center justify-center bg-slate-50 px-6 py-12 lg:w-1/2">

        <div className="w-full max-w-md">

          {/* LOGO MOBILE */}
          <div className="mb-8 lg:hidden">

            <div className="flex items-center gap-3">

              <div className="rounded-xl bg-emerald-500 p-2 text-slate-950">
                <BrainCircuit
                  size={24}
                />
              </div>

              <strong className="text-slate-950">
                Gestão Inteligente
              </strong>

            </div>

          </div>


          <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
            Acesso ao sistema
          </p>

          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Entrar
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Informe suas credenciais para
            acessar sua conta.
          </p>


          <form
            onSubmit={handleSubmit}
            className="mt-8 space-y-5"
          >

            {/* E-MAIL */}
            <div>

              <label className="mb-2 block text-sm font-medium text-slate-700">
                E-mail
              </label>


              <div className="relative">

                <Mail
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />


                <input
                  required
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) =>
                    setEmail(
                      event.target.value
                    )
                  }
                  placeholder="seu@email.com"
                  className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-11 pr-4 outline-none transition focus:border-emerald-500"
                />

              </div>

            </div>


            {/* SENHA */}
            <div>

              <label className="mb-2 block text-sm font-medium text-slate-700">
                Senha
              </label>


              <div className="relative">

                <LockKeyhole
                  size={18}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
                />


                <input
                  required
                  type={
                    mostrarSenha
                      ? "text"
                      : "password"
                  }
                  autoComplete="current-password"
                  value={senha}
                  onChange={(event) =>
                    setSenha(
                      event.target.value
                    )
                  }
                  placeholder="Sua senha"
                  className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-11 pr-12 outline-none transition focus:border-emerald-500"
                />


                <button
                  type="button"
                  onClick={() =>
                    setMostrarSenha(
                      (current) =>
                        !current
                    )
                  }
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                  aria-label={
                    mostrarSenha
                      ? "Ocultar senha"
                      : "Mostrar senha"
                  }
                >

                  {mostrarSenha ? (
                    <EyeOff
                      size={18}
                    />
                  ) : (
                    <Eye
                      size={18}
                    />
                  )}

                </button>

              </div>

            </div>


            {/* ERRO */}
            {erro && (
              <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {erro}
              </div>
            )}


            {/* BOTÃO */}
            <button
              type="submit"
              disabled={carregando}
              className="w-full rounded-xl bg-emerald-500 px-5 py-3 font-bold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {carregando
                ? "Entrando..."
                : "Entrar"}
            </button>

          </form>


          <div className="mt-8 rounded-xl border border-slate-200 bg-white p-4">

            <p className="text-xs leading-5 text-slate-500">
              O acesso ao sistema depende
              do perfil atribuído à conta:
              administrador, vendedor ou
              aluno.
            </p>

          </div>

        </div>

      </section>

    </main>
  );
}