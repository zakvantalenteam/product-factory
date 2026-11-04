# Stack pack: React 19, TypeScript 5, Vite

Read once, at the start, by the agents that design, write or review a React and TypeScript front end. The repo's own
rules, the UI standard (`.claude/core/reference/standards/ui.md`) and the approved prototype win over this pack.

## TypeScript
- `strict` on; no `any` (use `unknown` and narrow), no non-null `!` without a reason; types for API calls come from
  the OpenAPI contract (generated or matched exactly).
- Discriminated unions for states (`{ status: "loading" } | { status: "error"; error: Problem } | ...`) with an
  exhaustive `switch` (a `never` check).
- `readonly` props and arrays where nothing mutates them; `as const` for literal tables.

## React 19
- Function components and hooks only; components pure during render (no side effects, no mutation of props or
  state); keys stable ids, never the array index for lists that change.
- Server state through the repo's query client (TanStack Query or the base's), keyed by everything that scopes the
  data (tenant, user, language, filters); never copy server data into `useState`.
- `useEffect` only to sync with something outside React; every effect cleans up (abort fetches, remove listeners);
  derive values during render instead of syncing state; `useMemo`/`useCallback` only for a measured cost or a
  stable dependency.
- React 19: `use` and Actions (`useActionState`, `useOptimistic`, form actions) where the repo already uses them;
  `ref` as a prop (no `forwardRef` in new code).
- Error boundaries around routes; Suspense with a skeleton for lazy routes (`React.lazy`).

## Safety
- Never `dangerouslySetInnerHTML` with untrusted text (user input, LLM output) unless it passes the repo's
  sanitiser; links from data allow `http:` and `https:` only; no tokens in `localStorage`.

## Accessibility and UI
- Semantic elements first (`button`, `a`, `label`, `table`); ARIA only when no element fits; focus managed for
  dialogs and route changes; `:focus-visible` for the ring; WCAG 2.2 AA contrast and 24x24 px targets.
- Every screen has loading, empty, error (problem-details mapped to translated text), no-permission and many-rows
  states; text through the i18n keys; theme tokens only.

## Speed and build
- Core Web Vitals budgets: LCP under 2.5 s, INP under 200 ms, CLS under 0.1; route-level code splitting; lists over
  ~200 rows virtualised or paged; images sized.
- Vite: env values through `import.meta.env.VITE_*` (never a secret: everything in the bundle is public).

## Tests
- Where tests live: the repo's test folder, mirroring the source path (`src/components/Card.tsx` ->
  `src/__tests__/components/Card.test.tsx`, or `tests/components/Card.test.tsx` when the repo uses `tests/`; a new repo
  uses `tests/`); never in the repo root or next to production code in a folder that ships.
- Vitest and Testing Library as the repo uses them: query by role and label, assert what the user sees, mock the
  network at the fetch layer (MSW or the repo's helper), no snapshot-only tests.
