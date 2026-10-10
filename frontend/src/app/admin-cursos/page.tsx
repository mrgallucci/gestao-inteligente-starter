import {
  redirect,
} from "next/navigation";

import CourseContentAdmin from "@/components/course-content-admin";

import {
  serverApi,
} from "@/lib/server-api";

import {
  getHomeForRole,
} from "@/lib/permissions";


type Course = {
  id: number;
  nome: string;
  produto: string;
  ativo: boolean;
};


async function getCourses():
  Promise<Course[]> {

  const response =
    await serverApi(
      "/api/courses"
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
      "Não foi possível carregar os cursos."
    );
  }


  return response.json();
}


export default async function AdminCoursesPage() {
  const courses =
    await getCourses();


  return (
    <div className="mx-auto max-w-7xl">

      <header className="mb-8">

        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Administração LMS
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-950">
          Conteúdo dos cursos
        </h1>

        <p className="mt-2 text-slate-500">
          Cadastre, edite e organize
          apostilas, vídeos e materiais.
        </p>

      </header>


      {courses.length > 0 ? (

        <CourseContentAdmin
          courses={courses}
        />

      ) : (

        <div className="rounded-2xl border border-dashed border-slate-300 p-10 text-center">

          <p className="font-semibold text-slate-800">
            Nenhum curso cadastrado.
          </p>

          <p className="mt-2 text-sm text-slate-500">
            Cadastre um curso antes
            de adicionar conteúdos.
          </p>

        </div>

      )}

    </div>
  );
}