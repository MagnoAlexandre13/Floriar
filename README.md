# Petal & Stem

A responsive, buildless boutique florist storefront. The storefront is in `dist/`; it uses plain HTML, CSS, and JavaScript, with no runtime dependencies or external font/image requests. An optional local Python REST backend is available in `backend/`.

## Backend Python — execução local

O projeto agora inclui uma API REST com **FastAPI e SQLite**, catálogo inicial,
criação e consulta de pedidos, atualização de estado e validação das entregas.
Inclui cadastro, login e logout com sessão em cookie HttpOnly. Cada cliente
acessa apenas seus pedidos; administradores gerenciam as etapas de todos eles.
O backend é organizado em `routes/`, `controllers/`, `queries/` e `schemas/`.
A loja e o cliente demonstrativo usam português do Brasil, inclusive datas,
nomes dos buquês e mensagens. Os valores continuam em dólares americanos (USD)
e a entrega ilustrativa mantém a área de Portland.
Requer Python 3.11 ou superior. Na pasta `petal-and-stem`, execute:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010
```

- **Cliente da API:** http://127.0.0.1:8010/cliente
- **Entrar ou cadastrar:** http://127.0.0.1:8010/conta.html
- **Documentação interativa:** http://127.0.0.1:8010/docs
- **Contrato OpenAPI JSON:** http://127.0.0.1:8010/openapi.json
- **Loja original:** http://127.0.0.1:8010/

O banco `backend/data/store.sqlite3` é criado automaticamente na primeira
inicialização. Os pedidos persistem após reiniciar o servidor. A página `/cliente`
consome a API e cria pedidos demonstrativos no banco. A loja original em `/`
continua com seu carrinho local e não envia pedidos à API. Não há pagamento ou
entrega real em nenhum dos fluxos. Não é necessário iniciar o servidor Node para
usar a API e o cliente Python.

Cadastre sua conta em `/conta.html`. Para tornar uma conta administradora,
execute no terminal local (substituindo o e-mail pela conta cadastrada):

```powershell
.venv\Scripts\python.exe -m backend.create_admin --email seu-email@example.com --promote
```

Não há conta administrativa ou senha padrão. O catálogo e o carrinho local
continuam públicos; a criação e consulta de pedidos na API exigem login.
Se usar `npm run dev`, mantenha o backend na porta 8010: o servidor Node
encaminha as requisições da API e mantém o acesso pela porta 4173.

Veja [documentação do backend e exemplos JSON](backend/README.md) e
[diagramas do projeto](docs/DIAGRAMAS.md).

Para testar o backend:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py" -v
```

## Run locally

```sh
npm install
npm run dev
```

Open **http://127.0.0.1:4173**. To deploy with another static host, publish the `dist/` folder. Product pages use bookmarkable hash routes, so no server rewrite rules are needed.

## Experience

- Editorial homepage with original floral imagery, seasonal collection, occasion shortcuts, studio story, subscription planner, delivery FAQs, and policy dialogs.
- Five bouquet pages, including sunflowers, each with two photographs, varieties, palette, dimensions, small/medium/large sizes, color choices, a required description of the desired arrangement, a gift card, and an optional glass vase.
- Combined occasion, budget, color, and availability filters, plus a three-step bouquet finder that respects the shopper’s budget.
- A delivery checker with sample Portland ZIP coverage, transparent per-bouquet fees, preparation lead times, closed days, capacity restrictions, and a rolling 30-day booking window.
- A persistent shopping bag with quantities, removal, editable gift messages and delivery dates, stale-date validation, and an honest sample review screen.
- A locally saved subscription plan. Saving does not start a subscription.
- Keyboard-operable dialogs, focus management, native labeled forms, visible focus, reduced-motion support, responsive images, and self-hosted fonts.

## Prototype boundaries

This is a fictional business. The studio story, prices in USD, contact details, opening hours, products, capacity, and Portland delivery area are illustrative. No order is created, no payment is requested or taken, and no subscription is activated. Bag and plan choices are stored only in the visitor’s browser. A real shop must connect inventory, live delivery coverage and capacity, address validation, tax calculation, a payment provider with guest checkout, and order/subscription management. Replace the sample policies and business details before accepting real purchases.

Delivery dates use `America/Los_Angeles` (Portland), independently of the visitor’s timezone. ZIP codes 97201–97202 cost $6; 97203–97206 cost $9. Each bouquet incurs a delivery fee. Standard preparation is two days; Wild at Heart needs five. Sunday and Monday are closed. The date ten days ahead is a sample fully booked date when it falls on an open day. Stored dates are checked again before review.

## Validation

```sh
npm run check
npm test
npx playwright test
```

The browser tests use installed Microsoft Edge (`channel: 'msedge'`). They cover the full bag journey, delivery errors, stale dates, filters, finder recommendations, keyboard dismissal, subscription persistence, narrow layouts, image loading, corrupt storage, and automated WCAG checks with axe. `node scripts/inspect-site.mjs` creates local desktop and mobile screenshots in `.cache/` for visual review. Automated accessibility checks complement manual review; they do not certify every assistive-technology combination.

## Artwork and typography

All floral images were created with the **built-in imagegen tool**, then copied into `dist/assets/` and compressed to WebP. The original outputs remain untouched in the generation directory. Production artwork:

| File | Subject |
| --- | --- |
| `dist/assets/hero.webp` | Sunlit loose garden arrangement in terracotta |
| `dist/assets/studio.webp` | Candid florist’s workbench |
| `dist/assets/sunday-morning.webp` | Cream and butter-yellow bouquet |
| `dist/assets/garden-party.webp` | Peach, pink, and coral bouquet |
| `dist/assets/softly-spoken.webp` | Blush and mauve bouquet |
| `dist/assets/wild-at-heart.webp` | Burgundy and rust bouquet |
| `dist/assets/sunflower.webp` | Buquê de girassóis amarelos, margaridas e eucalipto |
| `dist/assets/*-detail.webp` | Matching overhead photographs for each bouquet |
| `dist/assets/*-small.webp` | Optimized responsive product thumbnails |

The final generation prompts are recorded in [ARTWORK.md](ARTWORK.md). Cormorant Garamond and DM Sans are self-hosted under their included SIL Open Font Licenses in `dist/assets/`. The flower mark and botanical line drawing are native SVG artwork.

## Source map

- `dist/index.html`: homepage, navigation, and dialog shells.
- `dist/styles.css`: visual system and responsive layouts.
- `dist/shop.js`: sample catalog, pricing, date rules, filters, and data validation.
- `dist/app.js`: page routing, forms, dialogs, finder, bag, and local persistence.
- `.openai/hosting.json`: registered Sites identity and static output configuration.

No build step is required. `npm` dependencies are exclusively for development validation.
