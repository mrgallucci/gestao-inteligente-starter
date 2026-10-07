import type { Metadata } from "next";
import "./globals.css";
import AuthProvider from "@/components/auth-provider";
import AppShell from "@/components/app-shell";

export const metadata: Metadata = {
  title: "Gestão Inteligente | SARGTECH",
  description: "CRM, vendas, BI, LMS e inteligência comercial para a operação SargLab",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body>
  <AuthProvider>
    <AppShell>
      {children}
    </AppShell>
  </AuthProvider>
</body>
    </html>
  );
}
