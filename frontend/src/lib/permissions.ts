export function getHomeForRole(role: string) {
  switch (role) {
    case "admin": return "/";
    case "vendedor": return "/leads";
    case "aluno": return "/minha-area";
    default: return "/login";
  }
}

export function canAccessPath(role: string, pathname: string) {
  if (role === "admin") return true;

  if (role === "vendedor") {
    return (
      pathname.startsWith("/leads") ||
      pathname.startsWith("/funil") ||
      pathname.startsWith("/followups") ||
      pathname.startsWith("/sales") ||
      pathname.startsWith("/omnichannel") ||
      pathname.startsWith("/automacoes") ||
      pathname.startsWith("/workshop")
    );
  }

  if (role === "aluno") {
    return pathname.startsWith("/minha-area") || pathname.startsWith("/aluno/");
  }

  return false;
}
