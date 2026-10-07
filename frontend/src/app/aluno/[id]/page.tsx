"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, LoaderCircle } from "lucide-react";
import StudentCourse from "@/components/student-course";
import { clientApi } from "@/lib/client-api";

type Content = { id: number; titulo: string; tipo: string; ordem: number; duracao_minutos: number | null; descricao: string | null; url_conteudo: string | null; progresso: number; aberto_em: string | null; ultima_atividade_em: string | null; concluido_em: string | null };
type Enrollment = { id: number; lead_id: number; aluno: string; course_id: number; curso: string; descricao: string | null; status: string; progresso: number; acesso_liberado_em: string; primeiro_acesso_em: string | null; ultimo_acesso_em: string | null; concluido_em: string | null; conteudos: Content[] };

export default function StudentPage() {
  const params = useParams();
  const router = useRouter();
  const enrollmentId = String(params.id);
  const [enrollment, setEnrollment] = useState<Enrollment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadEnrollment() {
      try {
        const response = await clientApi(`/api/enrollments/${enrollmentId}`);
        const data = await response.json();
        if (response.status === 401) { router.replace("/login"); return; }
        if (response.status === 403) { setError(data.detail ?? "Você não possui acesso a esta matrícula."); return; }
        if (response.status === 404) { setError("Matrícula não encontrada."); return; }
        if (!response.ok) { setError(data.detail ?? "Não foi possível carregar o curso."); return; }
        setEnrollment(data);
      } catch {
        setError("Não foi possível conectar ao servidor.");
      } finally {
        setLoading(false);
      }
    }
    if (enrollmentId) loadEnrollment();
  }, [enrollmentId, router]);

  if (loading) return <div className="flex min-h-[60vh] items-center justify-center"><div className="text-center"><LoaderCircle size={36} className="mx-auto animate-spin text-emerald-500" /><p className="mt-4 text-sm text-slate-500">Carregando curso...</p></div></div>;
  if (error) return <div className="mx-auto max-w-xl"><div className="rounded-2xl border border-red-200 bg-red-50 p-6"><h1 className="text-lg font-bold text-red-800">Não foi possível abrir o curso</h1><p className="mt-2 text-sm text-red-700">{error}</p><button type="button" onClick={() => router.back()} className="mt-5 flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white"><ArrowLeft size={16} />Voltar</button></div></div>;
  if (!enrollment) return null;
  return <StudentCourse enrollment={enrollment} />;
}
