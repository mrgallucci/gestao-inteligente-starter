import { protectedJson } from "@/lib/server-protected";
import Link from "next/link";
import ProductForm from "@/components/product-form";

type Product = {
  id: number;
  nome: string;
  descricao: string | null;
  preco: number;
  ativo: boolean;
  criado_em: string;
  curso_id: number | null;
  curso_nome: string | null;
  curso_ativo: boolean | null;
  libera_lms: boolean;
};

async function getProducts(): Promise<Product[]> {
  return protectedJson<Product[]>("/api/products", "Não foi possível carregar os produtos.");
}

const money = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

export default async function ProductsPage() {
  const products = await getProducts();

  return (
    <div className="mx-auto max-w-7xl">
      <header className="mb-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-cobalt-600">
          Catálogo
        </p>

        <h1 className="mt-1 text-3xl font-bold text-midnight">
          Produtos
        </h1>

        <p className="mt-2 text-slate-500">
          Produtos disponíveis para comercialização.
        </p>
      </header>

      <ProductForm />

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {products.map((product) => (
          <article
            key={product.id}
            className="rounded-card border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase text-slate-400">
              Produto #{product.id}
            </p>

            <h2 className="mt-2 text-xl font-bold text-midnight">
              {product.nome}
            </h2>

            <p className="mt-3 text-sm text-slate-500">
              {product.descricao ||
                "Sem descrição cadastrada."}
            </p>

            <p className="mt-6 text-2xl font-bold text-cobalt-600">
              {money.format(product.preco)}
            </p>

            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className={product.ativo ? "inline-block rounded-full bg-success/10 px-3 py-1 text-xs font-semibold text-success" : "inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600"}>
                {product.ativo ? "Ativo" : "Inativo"}
              </span>
            </div>

            <div className="mt-4 rounded-xl border border-slate-200 bg-ice p-3 text-sm">
              {product.curso_id !== null ? (
                <>
                  <p className="text-xs font-semibold text-slate-500">Curso vinculado</p>
                  <p className="mt-1 font-semibold text-midnight">{product.curso_nome}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {product.curso_ativo
                      ? "Vendas pagas liberam acesso no LMS."
                      : "Curso inativo: vendas não liberam acesso."}
                  </p>
                </>
              ) : (
                <>
                  <p className="font-semibold text-slate-700">Este produto não libera curso.</p>
                  <Link href={`/admin-cursos?produto=${product.id}`} className="mt-1 inline-block text-xs font-semibold text-cobalt-600 underline">
                    Criar curso para este produto
                  </Link>
                </>
              )}
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}