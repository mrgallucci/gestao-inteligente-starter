import {
  cookies,
} from "next/headers";


const API_URL =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function serverApi(
  path: string,
  init: RequestInit = {}
) {
  const cookieStore =
    await cookies();


  const token =
    cookieStore.get(
      "gi_access_token"
    )?.value;


  const headers =
    new Headers(
      init.headers
    );


  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }


  return fetch(
    `${API_URL}${path}`,
    {
      ...init,

      headers,

      cache:
        init.cache ??
        "no-store",
    }
  );
}