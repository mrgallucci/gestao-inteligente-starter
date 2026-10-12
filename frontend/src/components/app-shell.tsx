"use client";

import {
  ReactNode,
  useEffect,
} from "react";

import {
  usePathname,
  useRouter,
} from "next/navigation";

import Sidebar from "@/components/sidebar";

import {
  useAuth,
} from "@/components/auth-provider";

import {
  canAccessPath,
  getHomeForRole,
} from "@/lib/permissions";


export default function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  const pathname =
    usePathname();

  const router =
    useRouter();

  const {
    user,
    loading,
  } = useAuth();


  const publicRoute =
    pathname === "/login";


  useEffect(() => {
    if (loading) {
      return;
    }

    if (!user) {
      if (!publicRoute) {
        router.replace(
          "/login"
        );
      }

      return;
    }

    if (publicRoute) {
      router.replace(
        getHomeForRole(
          user.role
        )
      );

      return;
    }

    if (
      !canAccessPath(
        user.role,
        pathname
      )
    ) {
      router.replace(
        getHomeForRole(
          user.role
        )
      );
    }

  }, [
    loading,
    user,
    pathname,
    publicRoute,
    router,
  ]);


  if (publicRoute) {
    return <>{children}</>;
  }


  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-midnight">

        <div className="text-center">

          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-700 border-t-cobalt-400" />

          <p className="mt-4 text-sm text-slate-400">
            Verificando sessão...
          </p>

        </div>

      </div>
    );
  }


  if (!user) {
    return (
      <div className="min-h-screen bg-midnight" />
    );
  }


  if (
    !canAccessPath(
      user.role,
      pathname
    )
  ) {
    return (
      <div className="min-h-screen bg-midnight" />
    );
  }


  return (
    <div className="flex min-h-screen bg-ice">

      <Sidebar />

      <main className="min-w-0 flex-1 p-6 lg:p-8">
        {children}
      </main>

    </div>
  );
}