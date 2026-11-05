# Petal & Stem

A responsive, buildless boutique florist storefront. The finished application is in `dist/`; it uses plain HTML, CSS, and JavaScript, with no runtime dependencies or external font/image requests.

## Run locally

```sh
npm install
npm run dev
```

Open **http://127.0.0.1:4173**. To deploy with another static host, publish the `dist/` folder. Product pages use bookmarkable hash routes, so no server rewrite rules are needed.

## Experience

- Editorial homepage with original floral imagery, seasonal collection, occasion shortcuts, studio story, subscription planner, delivery FAQs, and policy dialogs.
- Four bouquet pages, each with two photographs, varieties, palette, dimensions, three clearly described sizes, a gift card, and an optional glass vase.
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
