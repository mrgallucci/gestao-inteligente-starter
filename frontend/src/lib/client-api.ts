export async function clientApi(
  path: string,
  init: RequestInit = {}
) {
  return fetch(`/api/backend${path}`, {
    ...init,
    cache: init.cache ?? "no-store",
  });
}
