import { protectedJson } from "@/lib/server-protected";
import ProductForm from "@/components/product-form";

type Product = {
  id: number;
  nome: string;
  descricao: string | null;
  preco: number;
  ativo: boolean;
  criado_em: string;
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
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-600">
          Catálogo
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-950">
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
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <p className="text-xs font-semibold uppercase text-slate-400">
              Produto #{product.id}
            </p>

            <h2 className="mt-2 text-xl font-bold text-slate-950">
              {product.nome}
            </h2>

            <p className="mt-3 text-sm text-slate-500">
              {product.descricao ||
                "Sem descrição cadastrada."}
            </p>

            <p className="mt-6 text-2xl font-bold text-emerald-600">
              {money.format(product.preco)}
            </p>

            <span className="mt-4 inline-block rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">
              {product.ativo ? "Ativo" : "Inativo"}
            </span>
          </article>
        ))}
      </section>
    </div>
  );
}