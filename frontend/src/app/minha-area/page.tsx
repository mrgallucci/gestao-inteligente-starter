"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BookOpen, GraduationCap } from "lucide-react";
import { useRouter } from "next/navigation";
import { clientApi } from "@/lib/client-api";

type Enrollment = { id: number; course_id: number; curso: string; descricao: string | null; status: string; progresso: number };

export default function MyAreaPage() {
  const router = useRouter();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const response = await clientApi("/api/my/enrollments");
        const data = await response.json();
        if (response.status === 401) { router.replace("/login"); return; }
        if (!response.ok) { setError(data.detail ?? "Não foi possível carregar seus cursos."); return; }
        setEnrollments(data);
      } catch {
        setError("Não foi possível conectar ao servidor.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [router]);

  if (loading) return <p className="text-slate-500">Carregando seus cursos...</p>;

  return <div className="mx-auto max-w-6xl">
    <header className="mb-8"><p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">Área do aluno</p><h1 className="mt-1 text-3xl font-bold text-slate-950">Meus cursos</h1><p className="mt-2 text-slate-500">Continue seus estudos de onde parou.</p></header>
    {error && <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">{error}</div>}
    {!error && enrollments.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center"><GraduationCap size={36} className="mx-auto text-slate-400" /><p className="mt-4 font-semibold text-slate-800">Nenhum curso disponível.</p><p className="mt-2 text-sm text-slate-500">Você ainda não possui matrículas liberadas.</p></div>}
    <div className="grid gap-5 md:grid-cols-2">{enrollments.map((item) => <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex items-start gap-4"><div className="rounded-xl bg-emerald-50 p-3 text-emerald-600"><BookOpen size={24} /></div><div className="min-w-0 flex-1"><h2 className="font-bold text-slate-950">{item.curso}</h2><p className="mt-2 text-sm text-slate-500">{item.descricao}</p></div></div><div className="mt-6"><div className="mb-2 flex justify-between text-xs"><span className="text-slate-500">Progresso</span><strong>{item.progresso.toFixed(0)}%</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${Math.min(item.progresso, 100)}%` }} /></div></div><div className="mt-5 flex items-center justify-between gap-3"><span className="text-sm font-semibold text-slate-500">{item.status}</span><Link href={`/aluno/${item.id}`} className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">Acessar curso</Link></div></div>)}</div>
  </div>;
}
