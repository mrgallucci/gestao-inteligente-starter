import { expect, test, type Page } from "@playwright/test";

const API = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin-e2e@exemplo.local";
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? "senha-e2e-forte-123";
const RUN = Date.now().toString().slice(-6);

test.beforeAll(async ({ request }) => {
  // Cria o admin apenas se ainda não existir (bootstrap só funciona com banco sem usuários).
  await request.post(`${API}/api/auth/bootstrap-admin`, {
    data: { nome: "Admin E2E", email: ADMIN_EMAIL, senha: ADMIN_PASSWORD },
  });
});

/**
 * Login único para todos os testes. Só retorna depois que a navegação saiu de /login,
 * ou seja, depois que o cookie de sessão foi criado — evita a race de ir para outra
 * página antes de a sessão existir. Cada teste usa o seu próprio `page` (sem compartilhar
 * page/context entre testes).
 */
async function loginAsAdmin(page: Page) {
  await page.goto("/login");
  await page.getByPlaceholder("seu@email.com").fill(ADMIN_EMAIL);
  await page.getByPlaceholder("Sua senha").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: /entrar/i }).click();
  await expect(page).not.toHaveURL(/\/login/);
}

test("Login admin → Produto → Curso → Lead → Venda Paga → Matrícula", async ({ page }) => {
  const produto = `Produto E2E ${RUN}`;
  const curso = `Curso E2E ${RUN}`;
  const lead = `Lead E2E ${RUN}`;

  // 1. Login
  await loginAsAdmin(page);

  // 2. Produto (sem curso ainda)
  await page.goto("/products");
  await page.getByLabel("Nome").fill(produto);
  await page.getByLabel("Preço").fill("47");
  await page.getByRole("button", { name: "Cadastrar produto" }).click();
  await expect(page.getByText("Produto cadastrado!")).toBeVisible();
  const card = page.locator("article", { hasText: produto });
  await expect(card.getByText("Este produto não libera curso.")).toBeVisible();

  // 3. Curso vinculado pela interface.
  // A mensagem de sucesso do formulário é transitória (router.refresh() remonta a árvore
  // porque o produto deixa de estar na lista de "sem curso"). Por isso o teste valida a
  // RESPOSTA do POST e, depois, a consequência persistente em /products.
  await card.getByRole("link", { name: "Criar curso para este produto" }).click();
  await page.getByLabel("Nome do curso *").fill(curso);
  const [courseResponse] = await Promise.all([
    page.waitForResponse(
      (response) =>
        response.url().includes("/api/backend/api/courses") &&
        response.request().method() === "POST",
    ),
    page.getByRole("button", { name: "Criar curso" }).click(),
  ]);
  expect(courseResponse.ok(), `POST /api/courses retornou ${courseResponse.status()}`).toBeTruthy();

  await page.goto("/products");
  await expect(page.locator("article", { hasText: produto }).getByText("Curso vinculado")).toBeVisible();
  await expect(page.locator("article", { hasText: produto }).getByText(curso)).toBeVisible();

  // 4. Lead
  await page.goto("/leads");
  await page.getByLabel("Nome").first().fill(lead);
  await page.getByLabel("Objetivo").fill("Validar fluxo E2E");
  await page.getByRole("button", { name: "Cadastrar Lead" }).click();
  await expect(page.getByText("Lead cadastrado com sucesso!")).toBeVisible();

  // 5. Venda Paga: a tela avisa ANTES de confirmar que libera o curso
  await page.goto("/sales");
  await page.getByLabel("Cliente").selectOption({ label: lead });
  await page.getByLabel("Produto").selectOption({ label: produto });
  await expect(page.getByText("Esta venda liberará acesso ao LMS")).toBeVisible();
  await expect(page.getByText(curso, { exact: false }).first()).toBeVisible();
  await page.getByRole("button", { name: "Registrar venda" }).click();
  await expect(page.getByText("Venda registrada com sucesso!")).toBeVisible();

  // 6. Listagem mostra a entrega e o LMS mostra a matrícula
  const row = page.locator("tr", { hasText: lead });
  await expect(row.getByText("LMS", { exact: true })).toBeVisible();
  await expect(row.getByText("Acesso liberado", { exact: true })).toBeVisible();
  await page.goto("/lms");
  await expect(page.getByText(lead).first()).toBeVisible();
});

test("Produto sem curso: venda permitida, sem matrícula e explícito na interface", async ({ page }) => {
  const produto = `Livro E2E ${RUN}`;
  const lead = `Lead sem curso ${RUN}`;

  await loginAsAdmin(page);

  await page.goto("/products");
  await page.getByLabel("Nome").fill(produto);
  await page.getByLabel("Preço").fill("19.9");
  await page.getByRole("button", { name: "Cadastrar produto" }).click();
  await expect(page.getByText("Produto cadastrado!")).toBeVisible();

  await page.goto("/leads");
  await page.getByLabel("Nome").first().fill(lead);
  await page.getByLabel("Objetivo").fill("Sem curso");
  await page.getByRole("button", { name: "Cadastrar Lead" }).click();
  await expect(page.getByText("Lead cadastrado com sucesso!")).toBeVisible();

  await page.goto("/sales");
  await page.getByLabel("Cliente").selectOption({ label: lead });
  await page.getByLabel("Produto").selectOption({ label: produto });
  await expect(page.getByText("Este produto não libera curso.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Registrar venda" }).click();
  await expect(page.getByText("Venda registrada com sucesso!")).toBeVisible();
  await expect(page.locator("tr", { hasText: lead }).getByText("Não aplicável")).toBeVisible();
});
