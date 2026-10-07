export type AuthUser = {
  id: number;
  nome: string;
  email: string;
  role: string;
  lead_id: number | null;
  ativo: boolean;
};
