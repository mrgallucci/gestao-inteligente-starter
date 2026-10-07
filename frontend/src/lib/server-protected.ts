import { redirect } from "next/navigation";

import { getHomeForRole } from "@/lib/permissions";
import { serverApi } from "@/lib/server-api";

export async function protectedJson<T>(
  path: string,
  errorMessage = "Não foi possível carregar os dados."
): Promise<T> {
  const response = await serverApi(path);

  if (response.status === 401) {
    redirect("/login");
  }

  if (response.status === 403) {
    const meResponse = await serverApi("/api/auth/me");

    if (meResponse.ok) {
      const me = await meResponse.json();
      redirect(getHomeForRole(me.role));
    }

    redirect("/login");
  }

  if (!response.ok) {
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}
