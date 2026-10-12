import {
  NextRequest,
  NextResponse,
} from "next/server";


export async function POST(
  request: NextRequest
) {
  try {
    const body =
      await request.json();


    const response =
      await fetch(
        `${process.env.BACKEND_URL ?? "http://127.0.0.1:8000"}/api/auth/login`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(body),

          cache: "no-store",
        }
      );


    const data =
      await response.json();


    if (!response.ok) {
      return NextResponse.json(
        data,
        {
          status:
            response.status,
        }
      );
    }


    const result =
      NextResponse.json({
        user: data.user,
      });


    result.cookies.set(
      "gi_access_token",
      data.access_token,
      {
        httpOnly: true,

        secure:
          process.env.NODE_ENV ===
          "production",

        sameSite: "lax",

        path: "/",

        // Mesma validade do JWT emitido pelo backend (fallback: 8 horas).
        maxAge:
          typeof data.expires_in === "number" && data.expires_in > 0
            ? data.expires_in
            : 60 * 60 * 8,
      }
    );


    return result;

  } catch {
    return NextResponse.json(
      {
        detail:
          "Não foi possível conectar ao servidor de autenticação.",
      },
      {
        status: 500,
      }
    );
  }
}