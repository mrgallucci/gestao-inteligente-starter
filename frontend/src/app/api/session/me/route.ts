import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


export async function GET() {
  try {
    const cookieStore =
      await cookies();

    const token =
      cookieStore.get(
        "gi_access_token"
      )?.value;


    if (!token) {
      return NextResponse.json(
        {
          detail:
            "Sessão não encontrada.",
        },
        {
          status: 401,
        }
      );
    }


    const response =
      await fetch(
        `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/auth/me`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          cache: "no-store",
        }
      );


    const data =
      await response.json();


    return NextResponse.json(
      data,
      {
        status:
          response.status,
      }
    );

  } catch {
    return NextResponse.json(
      {
        detail:
          "Não foi possível validar a sessão.",
      },
      {
        status: 500,
      }
    );
  }
}