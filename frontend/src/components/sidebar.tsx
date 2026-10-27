"use client";

import Link from "next/link";
import {
  BookOpenCheck,
  CalendarClock,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Megaphone,
  MessagesSquare,
  Package,
  Presentation,
  ShieldCheck,
  ShoppingCart,
  Sparkles,
  TrendingUp,
  UserRound,
  Users,
  WalletCards,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import BrandMark from "@/components/brand-mark";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard, roles: ["admin"] },
  { href: "/leads", label: "CRM / Leads", icon: Users, roles: ["admin", "vendedor"] },
  { href: "/funil", label: "Funil de vendas", icon: TrendingUp, roles: ["admin", "vendedor"] },
  { href: "/followups", label: "Follow-ups", icon: CalendarClock, roles: ["admin", "vendedor"] },
  { href: "/workshop", label: "Treinamento IA", icon: Presentation, roles: ["admin", "vendedor"] },
  { href: "/omnichannel", label: "Omnichannel", icon: MessagesSquare, roles: ["admin", "vendedor"] },
  { href: "/automacoes", label: "Automações", icon: Sparkles, roles: ["admin", "vendedor"] },
  { href: "/customer-analytics", label: "Customer Analytics", icon: UserRound, roles: ["admin"] },
  { href: "/sarglab-analytics", label: "SargLab / Captação", icon: BookOpenCheck, roles: ["admin"] },
  { href: "/marketing", label: "Marketing Analytics", icon: Megaphone, roles: ["admin"] },
  { href: "/financeiro", label: "Financeiro", icon: WalletCards, roles: ["admin"] },
  { href: "/products", label: "Produtos", icon: Package, roles: ["admin"] },
  { href: "/sales", label: "Vendas", icon: ShoppingCart, roles: ["admin", "vendedor"] },
  { href: "/lms", label: "LMS / Cursos", icon: GraduationCap, roles: ["admin"] },
  { href: "/admin-cursos", label: "Admin Cursos", icon: BookOpenCheck, roles: ["admin"] },
  { href: "/usuarios", label: "Usuários", icon: ShieldCheck, roles: ["admin"] },
  { href: "/minha-area", label: "Minha Área", icon: GraduationCap, roles: ["aluno"] },
];

function roleLabel(role: string) {
  if (role === "admin") return "Administrador";
  if (role === "vendedor") return "Vendedor";
  if (role === "aluno") return "Aluno";
  return role;
}

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    try {
      await fetch("/api/session/logout", { method: "POST" });
    } finally {
      logout();
      router.replace("/login");
      router.refresh();
    }
  }

  return <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col bg-midnight text-white">
    <div className="border-b border-slate-800 p-6">
      <div className="flex items-center gap-3"><BrandMark size={34} tone="dark" /><div><p className="font-bold">Gestão Inteligente</p><p className="text-[11px] text-slate-500">SARGTECH</p></div></div>
    </div>

    <nav className="flex-1 overflow-y-auto p-4"><div className="space-y-1">{items.filter((item) => user ? item.roles.includes(user.role) : false).map((item) => {
      const Icon = item.icon;
      const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
      return <Link key={item.href} href={item.href} className={active ? "flex items-center gap-3 rounded-xl bg-cobalt-500 px-4 py-3 text-sm font-semibold text-white" : "flex items-center gap-3 rounded-xl px-4 py-3 text-sm text-slate-300 transition hover:bg-slate-900 hover:text-white"}><Icon size={18} />{item.label}</Link>;
    })}</div></nav>

    {user && <div className="border-t border-slate-800 p-4"><div className="rounded-card bg-slate-900 p-4"><p className="truncate text-sm font-bold text-white">{user.nome}</p><p className="mt-1 truncate text-xs text-slate-500">{user.email}</p><div className="mt-3 inline-flex rounded-full bg-cobalt-400/10 px-2.5 py-1 text-xs font-semibold text-cobalt-400">{roleLabel(user.role)}</div><button type="button" onClick={handleLogout} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-700 px-3 py-2 text-sm font-semibold text-slate-300 transition hover:bg-slate-800 hover:text-white"><LogOut size={16} />Sair</button></div></div>}
  </aside>;
}
