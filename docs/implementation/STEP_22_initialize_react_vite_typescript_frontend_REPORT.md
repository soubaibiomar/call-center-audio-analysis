# STEP_22 — Initialize React Vite TypeScript frontend

**DONE — PASS WITH LIMITATIONS.** Owner: Platform / Codex. Date: 2026-10-31,
Africa/Casablanca. Branch: `feature/project28-foundation`. Working HEAD:
`a37e4634af1d2947fc3c548d54e62bda0b0daf89`; pinned original upstream:
`fed4b610742c1337147281fcec8f2cdcc0a79be5`. Windows 11, PowerShell,
uv-managed Python 3.12, Node 24.18.0 / npm 11.16.0, local Docker PostgreSQL,
isolated Redis and Chrome. No GPU inference, training, commit, push or public
deployment occurred.

## 1. Goal and plain-English explanation

Built an accessible application foundation with a shared sidebar/topbar, responsive
navigation, typed API access, real service-health checks and server-verified
protected routes. This gives the following frontend steps a consistent home.
The existing STEP_21 standalone reviewer was preserved at `/review-ui/`; the new
application lives at `/workspace/` and Gradio remains separate.

Read the master instructions, STEP_INDEX, complete STEP_22 prompt/template,
STEP_21 report, progress/limitations, design system/checklist and both approved
screenshots before implementation. STEP_21's local research workflow passed with
limitations; STEP_22 requires its API contracts and build tools, not production
emotion accuracy. Existing `/health`, `/ready` and `/api/v1/me` contracts were
available. Production OIDC onboarding and representative Darija accuracy remain
limitations. Local validation uses signed synthetic identities, not a production
identity-provider deployment.

The six protected feature pages are honest placeholders. No dashboards, live
audio, training tools, fake call counts or emotion analytics were implemented in
this step. The health screen is connected to the actual local FastAPI process.

## 2. Actual upstream versus upgraded implementation

| Area / exact path or symbol | Verified original upstream | Before STEP_22 | STEP_22 result and compatibility |
|---|---|---|---|
| `app.py`, `src/ui/app_builder.py:build_app` | Gradio Blocks, Whisper/workflow startup and tab assembly; no React app | Existing modified Gradio plus normalized backend | No changes to these files in STEP_22; regression suite retained |
| `apps/web/src/main.tsx`, `vite.config.js` | Absent | STEP_21 standalone emotion-review entry with `/review-ui/` base | Source hashes unchanged; old build and development command retained |
| `apps/web/workspace/`, `src/app/App.tsx:AppShell` | Absent | No common application shell | Separate Vite root/output, shared shell and seven navigation destinations |
| `src/app/App.tsx:RequireIdentity`, `auth.tsx` | No HTTP SPA guard | Review-specific token handling | New in-memory session for shell, verified by existing `/api/v1/me`; protected feature data not fetched |
| `src/lib/api/client.ts`, `generated.ts` | Absent | Feature-local handwritten review types | Generated Health/Identity types plus runtime checks; existing review contract unchanged |
| `services/api/app.py:create_app` | Absent in original | Optional `/review-ui` static mount | Additional optional `/workspace` static mount; API paths/auth boundary unchanged |
| `.github/workflows/ci.yml` | No frontend checks | Existing Python jobs | Separate locked frontend contract/lint/test/build job; Python jobs retained |

`git diff --stat` and `--name-status` are captured before/after in the evidence
directory. Final tracked cumulative diff: **40 files, 1,082 insertions and 369
deletions**. Most changes predate STEP_22. Ordinary Git diff omits the many
untracked platform/frontend files. Do not attribute the whole working-tree diff
to this step. `before-files.json` records pre-edit frontend/API/CI hashes;
`source-inventory.json` records the step's final paths and hashes. The original
upstream tree and Gradio entry/imports were inspected with `git ls-tree`/`git show`.

## 3. Files explained — created, modified and preserved

| File(s) | Change, interface and purpose |
|---|---|
| `apps/web/workspace/index.html`, `workspace/main.tsx` | New document and development-safe entry import; starts the shell independently of review |
| `apps/web/vite.workspace.config.ts` | New loopback server, `/workspace/` base, local API proxies and separate output directory |
| `apps/web/src/app/main.tsx` | New React root, StrictMode, QueryClientProvider, AuthProvider and HashRouter |
| `apps/web/src/app/App.tsx` | New AppShell, route map, RequireIdentity, ConnectPage, HealthPage, StatusCard, PageHeading and reserved WorkspacePage |
| `apps/web/src/app/auth.tsx` | New context, session state, server identity query, disconnect cancellation and cache clearing |
| `apps/web/src/app/workspace.css` | New reusable tokens, cards, tables, pills, layouts, focus and responsive/reduced-motion rules; Tailwind utilities |
| `apps/web/src/lib/api/client.ts` | New same-origin read client, safe ApiError messages and Health/Identity response validation |
| `apps/web/src/lib/api/generated.ts`, `scripts/generate-api.mjs` | New deterministic narrow API type generation with canonical OpenAPI fingerprint/check mode |
| `apps/web/src/app/App.test.tsx`, `src/lib/api/client.test.ts`, `tests/setup.ts`, `vitest.config.ts` | New component/client checks with cleanup and DOM assertions |
| `apps/web/package.json`, `package-lock.json`, `.gitignore`, `tsconfig.json`, `tsconfig.workspace.json` | Pinned dependencies/scripts, ignored build outputs, strict application/test configuration; stricter workspace index/unused/switch checks |
| `tests/frontend/workspace.mjs` | New actual-browser checks using existing Playwright/axe, synthetic identities and screenshots |
| `services/api/app.py` | Optional static build mount; no new API authorization bypass or schema path |
| `scripts/preview_emotion_reviews.py` | Optional private test-URL file overrides; existing defaults/test-database guard retained |
| `apps/web/tests/emotion-review.mjs` | Optional evidence-directory override to preserve historical STEP_21 captures |
| `tests/api/test_api.py`, `tests/integration/test_postgresql_persistence.py`, `tests/emotion/test_baseline.py` | Type annotations on reused synthetic fixture helpers; runtime behavior unchanged |
| `.github/workflows/ci.yml` | New frontend job: Node, npm ci, generated-contract check, lint, component tests and dual build |
| `docs/development/frontend-workspace.md`, this report, `PROGRESS.md`, `CURRENT_LIMITATIONS.md`, evidence directory | Setup, current status, limits and actual verification |
| `docs/implementation/STEP_21_collect_reviewed_emotion_labels_without_contaminating_d_REPORT.md` | Compatibility follow-up for optional helper arguments and repeated legacy proof |

No source/data files were deleted. `src/features/emotion/EmotionReview.tsx`,
its CSS, the original frontend main entry and review Vite config retain their
pre-step SHA-256 values. Review output remains 232,244 bytes JS / 6,708 bytes CSS.

## 4. Code explanation, algorithms and errors

`workspace/index.html → workspace/main.tsx → src/app/main.tsx` is the startup
chain. `createRoot` attaches React to a checked DOM root; StrictMode exposes
development lifecycle mistakes. QueryClientProvider owns server state;
AuthProvider owns the transient token; HashRouter maps the fragment to routes.
Hash fragments are not sent to FastAPI, so `/workspace/#/calls` reloads through
the same static index without accidentally rewriting an API URL.

`App` nests every page inside `AppShell`. A constant route table drives both
navigation and feature placeholders. Health and connect are public. Protected
routes sit inside `RequireIdentity`, which redirects a guest to the connection
form while preserving a validated destination. Pending verification renders a
status; failed verification renders a safe recovery form; only successful server
verification renders the protected outlet. Unknown routes provide a recovery link.
No role, tenant or user ID is taken from the browser's input.

`useSessionState` stores the token in React state and uses a generation number,
not token contents, in the identity query key. `connect` cancels old work, clears
cache, advances the generation and submits the new credential. `clear` removes
the token, cancels queries and removes cached data. Identity refetches on
focus/reconnect and every 60 seconds. The API remains authoritative between
checks; the shell's guard cannot replace server authorization. The access field
is immediately emptied on submit. Reload loses the session intentionally.

`client.ts:get` accepts only three fixed relative endpoints. It sends credentials
only as a bearer header on the identity request, omits cookies, refuses redirects,
uses no-store and combines caller cancellation with an eight-second timeout.
Transport/HTTP/JSON errors become safe status-based messages; response bodies,
tokens and internal server details are not reflected. `getHealth` requires the
correct endpoint-specific status. `getIdentity` requires UUID-shaped IDs and an
allowed server role before constructing the generated type.

The generator reads the reviewed OpenAPI snapshot. It requires the three GET
paths and only supports the string/enum object fields consumed here; unsupported
types fail generation. Required fields become required TypeScript properties,
enums become string unions. Canonical JSON hashing avoids CRLF/LF differences;
check mode compares normalized generated output without rewriting it. This is
deliberately not a universal OpenAPI generator. Runtime validation is still needed
because generated TypeScript types disappear when JavaScript runs.

`HealthPage` has independent liveness/readiness queries. A live process may be
unready because database/auth configuration is missing; these states stay
separate. Check again refetches both; pending state disables duplicate refreshes;
failed/offline checks stay visible. Its timestamp is the last successful liveness
check, not a claim of inference quality or uptime history.

Representative request block from `client.ts`:

```typescript
signal: AbortSignal.any([AbortSignal.timeout(8000), ...(signal ? [signal] : [])]),
headers: token ? { Authorization: `Bearer ${token}` } : {},
cache: "no-store",
credentials: "omit",
redirect: "error",
```

The first line bounds waiting and preserves cancellation. The second adds the
credential only for the verified-identity request. The last three prevent browser
cache reuse, cookie attachment and forwarding through redirects respectively.
The guard's final `return <Outlet />` is reached only after token presence,
pending verification and error branches have been handled; a successful page
render therefore depends on the server response, not a client-supplied role.

Navigation filtering operates on seven route names, O(number of routes), and
never searches customer data. Mobile navigation is an in-flow disclosure, not
a modal, so it needs no focus trap. Escape closes it and returns focus to the
menu button; route changes close it and focus the main landmark. The skip link
provides keyboard access to content. CSS grids collapse without horizontal
overflow; tables retain proper headers/captions. No charts or synthetic metrics
are needed to represent this foundation truthfully.

## 5. Imports and dependency explanation

Exact installed versions are also saved in `versions.json` and the npm lockfile.
Existing React/Vite/TypeScript versions were preserved rather than blindly upgraded.

| New import symbols | Origin / version | Meaning, call sites and alternatives |
|---|---|---|
| `StrictMode`, `createContext`, `useContext`, `useRef`, `useState`, `useEffect`, type `ReactNode`, type `FormEvent` | React 19.3.1 | Lifecycle checks, session/provider, local form/menu state, focus and event types; reuse existing React rather than introduce global-state tooling |
| `createRoot` | react-dom 19.3.1 | Mounts the new SPA; separate from old review root |
| `HashRouter`, `MemoryRouter`, `Link`, `NavLink`, `Navigate`, `Outlet`, `Route`, `Routes`, `useLocation` | react-router-dom 7.18.5 | Static-friendly routes, active navigation, guards, nested pages and isolated test history; BrowserRouter would require fallback hosting rules |
| `QueryClient`, `QueryClientProvider`, `useQuery`, `useQueryClient` | @tanstack/react-query 5.105.0 | Server-state ownership, fetching/status/cancellation, tests and cache clearing; avoids duplicated loading/error effects |
| `ArrowRight`, `ArrowSquareOut`, `BookOpen`, `CheckCircle`, `Flask`, `Gear`, `Heartbeat`, `List`, `LockKey`, `MagnifyingGlass`, `Phone`, `SignOut`, `SquaresFour`, `WarningCircle`, `Waveform` | @phosphor-icons/react 2.1.10 | One consistent decorative icon family; accessible names belong to surrounding controls, decorative icons are hidden |
| `defineConfig` | Vite 8.3.5; Vitest 5.0.5 in test config | Typed build/test configuration; keeps review and shell outputs separate |
| default `tailwindcss`; CSS `@import "tailwindcss"` | @tailwindcss/vite and tailwindcss 4.3.3 | Official Vite plugin, utility generation and shared theme variables; custom CSS expresses approved product composition |
| type `Health`, `Identity` | Local generated module | API DTOs from existing snapshot, with runtime validation in client |
| `App`, `AuthProvider`, `useSession`, `getHealth`, `getIdentity`, `ApiError`; CSS import and workspace entry side-effect import | Local modules | Component/provider/request boundaries explained above; no ML runtime |
| `expect`, `it`, `describe`, `vi`, `afterEach`; `render`, `screen`, `waitFor`, `cleanup`; default `userEvent`; jest-dom/vitest side-effect import | Vitest 5.0.5; Testing Library React 16.3.3, user-event 14.6.8, jest-dom 7.0.1; jsdom 30.1.3 | Component behavior, safe request stubs, real user input and DOM matchers; cleanup avoids cross-test state |
| `fileURLToPath`, `readFileSync`, `writeFileSync`, `readFile`, `mkdir`, `writeFile`, `createHash`, `createRequire`, default `assert` | Node standard library; @types/node 26.6.6 | Portable paths, deterministic contracts, evidence and browser assertions. Browser harness resolves dependencies from apps/web without a second npm project |
| `chromium`, default `AxeBuilder` via createRequire | Existing Playwright 1.64.1, @axe-core/playwright 4.14.0 | Actual Chrome interaction and automated WCAG-tag checks; no cloud browser |
| Python `os`; `CallReport` in two fixture modules | Standard library; local graph contract | Private test-file environment overrides; explicit fixture return/input types. Existing Session/Call imports type the reused database helper; audio helper uses built-in int/bool/bytes |

TypeScript remains **7.0.2**. Oxlint **1.90.0** provides actual React/accessibility
linting with warnings denied; strict compiler checks are separate. Initial npm
resolution rejected typescript-eslint's `<6.1` peer and openapi-typescript's `^5`
peer. No forced peer resolution or compiler downgrade was used. The small narrow
generator uses Node built-ins instead. These dependencies only build/test/render
the frontend; none trains a model.

Current official guidance was checked: [React SPA setup](https://react.dev/learn/build-a-react-app-from-scratch),
[Vite configuration](https://vite.dev/config/),
[React Router declarative setup](https://reactrouter.com/start/declarative/installation),
[TanStack cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation),
[Tailwind Vite installation](https://tailwindcss.com/docs/installation/using-vite),
[Vitest](https://vitest.dev/guide/) and [Oxlint](https://oxc.rs/docs/guide/usage/linter.html).
No SSR/SEO requirement justifies Next.js in this scoped internal SPA.

## 6. Concepts from first principles

React describes a screen as components of current state: when a health request
changes from pending to success, the same status card renders Connected. Vite
serves modules during development and bundles static files for deployment.
TypeScript rejects invalid data shapes during development, but cannot validate a
network response at runtime; that is why the client also checks values.

A router maps an address to a screen. Here the `#/calls` fragment selects Calls
without asking FastAPI to interpret it as an API path. A nested guard acts like
an entrance checkpoint for the screen, while real data authorization remains on
the server. TanStack Query tracks whether each server request is loading, stale,
failed or successful. Tailwind generates CSS utilities; tokens/custom CSS keep
their visual choices consistent with the approved screenshot.

Example: a guest opens `#/calls`, reaches the connection form, submits a synthetic
signed token, and the API verifies issuer/signature/account. The browser validates
the returned Identity and opens the Calls placeholder. Disconnect cancels pending
work and clears memory; returning to Calls requires a new connection. No call data
is loaded by that example, and no model learned anything.

## 7. Data, model, security and privacy

New consumed schemas are Health(status) and Identity(tenant_id, user_id, role).
No audio, customer records or training labels are read by the shell. Browser proof
uses synthetic users and the existing synthetic review fixture in an isolated
PostgreSQL database. Signed tokens are stored only under ignored `.local/` for
the test harness; screenshots/logs contain no token values. Source/dataset rights,
retention, uncertain diarization and research emotion/Darija limitations remain.

Same-origin fixed paths prevent arbitrary token destinations; redirects are
refused. React text rendering escapes strings and the client does not render API
HTML. Query cache is not persisted. A bearer token in JS memory still depends on
preventing XSS and secure browser operation. There is no refresh-token storage,
production login/PKCE flow, permission management, CSP rollout or public hosting
claim in this step. The API's server-side tenant and role checks remain intact.

Development binds loopback only. Production uses static files behind FastAPI's
existing headers/no-store boundary. GPU VRAM and ML accuracy: **Not measured in
this step**, because no inference or training ran. Existing service/model defaults
and Ollama were not stopped or reconfigured.

## 8. Tests, exact commands and observed results

Run frontend commands from repository root with `--prefix apps/web`:

| Command | Actual result |
|---|---|
| `npm run api:check --prefix apps/web` | Exit 0, generated snapshot check current |
| `npm run lint --prefix apps/web` | Exit 0, no warnings under React/accessibility lint |
| `npm run typecheck --prefix apps/web` | Exit 0; legacy strict and stricter shell configuration |
| `npm test --prefix apps/web` | Exit 0; **17 passed**, two files, Vitest duration **8.99s** |
| `npm run build --prefix apps/web` | Exit 0; both preserved review and new shell built |
| `node tests/frontend/workspace.mjs` | Exit 0; **17 browser assertions**, 10 screenshots, seven axe audits, zero unexpected JS errors, zero violations |
| `PROJECT28_REVIEW_EVIDENCE_DIR=…/legacy-review` then `node apps/web/tests/emotion-review.mjs` | Exit 0; six legacy workflow assertions, eight viewport captures, zero axe/console errors |
| Development browser smoke at `http://127.0.0.1:8783/workspace/#/health` | Real local API connected, zero page errors |
| `ruff check` / `ruff format --check` scoped Python files | Passed after formatting corrections |
| `mypy services/api/app.py scripts/preview_emotion_reviews.py --follow-imports=silent` | Exit 0, no issues in two source files after typing reused fixtures |
| Full configured backend command below | **453 passed, 2 skipped, 1 warning in 63.88s**, exit 0 |
| `npm audit --omit=dev --prefix apps/web --json` | Zero reported production vulnerabilities at check time |

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step22_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step22_test_app_url'
./.venv/Scripts/python.exe -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion -q --tb=short -rs
```

The two skips are existing real pgvector knowledge tests lacking
`PROJECT28_KNOWLEDGE_TEST_URL_FILE`; they are not passes. Existing pytest-asyncio
fixture-scope and Starlette/AnyIO deprecation messages remain. Actual regression
outputs are retained, including initial failures and final corrected execution.
The new GitHub CI job is configured; no remote CI run or push was performed.

Browser coverage includes real liveness/readiness, protected deep-link redirect,
invalid signed access (expected 401), successful server-verified identity,
six protected placeholders, navigation search/empty state, mobile disclosure,
Escape/focus return, keyboard skip link, disconnect, reload, not-found recovery,
injected offline state/retry, and the unchanged review entry. Offline failure is
intentional browser fault injection; signed/health requests otherwise reach the
actual local API. The seven axe audits are not a full manual WCAG certification.

## 9. Analytics and quantitative evidence

One final local build sample, same laptop, no GPU work. Full npm build wall time
includes strict checking and both outputs: **3.719s**. Vite-reported shell bundling:
**722ms**. Initial standalone review baseline: **179ms** Vite bundling; final
review bundling: 128ms. These are single observations of different workloads,
not a statistically established speedup or regression; p50/p95 are not measured.

| Static output | Raw bytes | Python gzip level-9 bytes, fixed mtime |
|---|---:|---:|
| Shell HTML | 589 | 339 |
| Shell JS | 354,220 | 107,219 |
| Shell CSS | 14,246 | 4,054 |
| Shell total | **369,055** | **111,612** |
| Existing review JS | 232,244 | 71,703 |
| Existing review CSS | 6,708 | 2,105 |

Bundle size is the sum of emitted static file bytes, not measured network usage
or memory. Vite's displayed gzip estimate uses different compression settings;
the JSON receipt specifies this measurement's exact method. The larger shell
contains routing, query and shared layout capabilities the review page lacked;
do not call that difference an equivalent-workload performance regression.

Browser route error count: **0** page errors/non-resource console errors during
17 assertions across public access/health/error screens and six protected pages.
Expected 401 and offline resource failures are tested separately. All captured
widths 1440/1280/1024/390 had **0 horizontal overflow**. Seven axe audits found
**0 violations**. These counts establish tested behavior only, not capacity,
uptime, assistive-technology completeness, real-call accuracy or load performance.

## 10. Technical questions with answers

1. **Why Vite instead of Next.js?** This is an internal SPA without a server-rendered
   SEO requirement. Separate static builds fit the existing FastAPI boundary;
   adding a second application server would increase scope.
2. **Why generated types plus runtime validation?** Generation catches contract
   drift during development/CI. Runtime checks catch malformed or mismatched
   server responses after TypeScript has been compiled away.
3. **Why keep the old review entry?** It already supports a tested correction
   workflow. Keeping separate roots/outputs avoids CSS/router regressions while
   the larger application grows.
4. **Why not persist access tokens?** Avoiding browser storage reduces persistence
   and accidental cross-session exposure. Reload requires reconnecting; a future
   production login flow must explicitly address that tradeoff.
5. **Why separate liveness and readiness?** An API process can answer requests
   while its database or identity configuration is unavailable. Showing Connected
   as a blanket Ready claim would mislead operators.
6. **What did the browser prove?** Real local API connection, server-verified access,
   route/error/keyboard/mobile behaviors and automated accessibility checks with
   synthetic data. It did not prove model quality or real identity-provider UX.
7. **Why no charts/call counts yet?** STEP_22 initializes the shell. STEP_23 connects
   dashboards to real data. Copying the reference's mock metrics would fabricate
   operational results.

## 11. Problems, decisions, risks and remaining work

- Resolved incompatible optional TypeScript tooling peers without force-installing
  or downgrading the working compiler: Oxlint plus a narrow generated DTO contract.
- Fixed a development-only entry URL that built successfully but returned 404 in
  Vite dev mode; a root-local entry imports the shared source. Actual dev smoke
  now passes. Initial lint/DOM-type issues were corrected, not ignored.
- Preview initially refused stale URL files that pointed outside a test database.
  Added optional test-file overrides and created separate test databases. The
  original role-membership test also requires its historical disposable prefix;
  a new compliant database was created rather than weakening its safety guard.
- Existing worker tests expected Redis on port 16379. A dedicated local test Redis
  was created; its first capability-restricted root entry failed to switch users,
  so it was relaunched explicitly as the Redis user with capabilities dropped.
  Worker/database affected checks then passed **28/28**. Existing Compose Redis
  was observed restarting and was not repaired/reconfigured in this frontend step.
- Extended strict checking found three old untyped synthetic helper calls. Added
  accurate fixture annotations; the scoped Python check now passes.
- Vite reports client-directive bundling warnings from TanStack/Router packages.
  This is an entirely client-rendered SPA; no React server-component semantics
  are relied on. Warnings remain visible in the build log; production/dev/browser
  execution passed.

Remaining boundaries: production OIDC/PKCE sign-in, CSP/deployment configuration,
container frontend packaging, dedicated knowledge-test service, real browser
assistive-technology audit, load testing and feature integrations are not completed
here. No refresh-token flow, role-management UI, customer search, call dashboards,
notifications or model training exists in these route placeholders. Existing
research-model and human-review constraints remain. No new release-readiness claim
is inferred from passing shell tests.

## 12. Deliverables, handoff and evidence checklist

**Decision: PASS WITH LIMITATIONS.** All three STEP_22 gates passed: development
and build work; health connects to the actual local API; authenticated route and
error states are tested. Proceed to **STEP_23 — Build dashboards for calls, live
and model lab**, after reading its prompt and checking its own dependencies.
STEP_23 was not started. Reuse the shell/tokens, shared request boundary and
query/cache lifecycle; connect real data before displaying metrics.

Next safe command: `npm run dev --prefix apps/web` (after the configured local
API is running). Setup and synthetic-test details are in the
[frontend runbook](../development/frontend-workspace.md).

- [x] Implementation, prerequisites, actual source comparison and file inventory recorded.
- [x] Code/dependencies explained; at least five answered questions.
- [x] Actual automated tests and failure corrections retained.
- [x] Synthetic-only screenshots, no tokens/customer data/model training.
- [x] Existing review source hashes/build/workflow preserved.
- [x] Progress/limitations updated; next step identified without advancing.
- [x] Screenshot/design checklist below completed.

Evidence root: [step22-20261031](evidence/step22-20261031/).
Key receipts: [frontend validation](evidence/step22-20261031/frontend-validation.json),
[backend final](evidence/step22-20261031/backend-regression-complete.txt),
[browser checks](evidence/step22-20261031/browser-qa.json),
[legacy review](evidence/step22-20261031/legacy-review/browser-qa.json),
[dev smoke](evidence/step22-20261031/dev-smoke.json),
[contrast](evidence/step22-20261031/contrast.json),
[versions](evidence/step22-20261031/versions.json),
[source inventory](evidence/step22-20261031/source-inventory.json).

## 13. Approved ERP UI design / visual contract verification

Visually inspected the primary
`design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` and secondary
`APPROVED_GREEN_ERP_REFERENCE.png`, then actual desktop/mobile renders. The
primary Commercially-style layout controls the design: light rounded sidebar,
neutral canvas, white rounded cards, quiet pill-shaped topbar/search/profile,
compact consistent icons, dark typography and green selected navigation/actions.
Product branding is Adaptive Call Center Intelligence; the reference's brand,
person, mock sales values and charts were not copied.

Routes/files: `/workspace/#/health`, `#/connect`, six guarded feature routes,
`src/app/App.tsx` and `workspace.css`. Existing `/review-ui/` and Gradio retain
their separate behavior. Search filters workspace pages rather than implying
customer search. Notifications/charts/filter widgets are intentionally absent
until they have real functionality. Status cards report real service checks;
the reserved pages explicitly explain their current scope.

| Acceptance check | Evidence and result |
|---|---|
| Neutral background, rounded white cards, green accent; no blue/pink defaults | PASS: canvas #F6F6F3, white #FFFFFF, forest #1D5B49, lime #9BE15D / selected #DDF2CB |
| Readable text, borders, spacing | PASS: text #182820, muted #56645D, borders #E4E8E1, 24–30px panels, 12–28px spacing |
| Sidebar/top search/profile, branding, pills/buttons | PASS: actual screenshots; search/filter and account states function |
| KPI-style cards and soft-header table | PASS: truthful service status cards, actual /health and /ready checks; no fabricated business KPIs |
| Charts | Not applicable to shell initialization; no chart library/default palette introduced |
| Responsive 1440/1280/1024/390 | PASS: four health captures, zero horizontal overflow; mobile menu/stacking verified |
| Keyboard, focus, reduced motion | PASS tested: keyboard-reachable skip link, route/main focus, Escape/menu focus return, visible green focus; animations/transitions disabled under reduced-motion rule |
| Contrast | Five principal text pairs all >=4.5:1: **15.405, 5.744, 7.940, 8.083, 6.115**; browser axe also found no contrast violations |
| Actual access/error/offline states | PASS: signed account, expected invalid access, not-found and injected network failure/retry |
| Premium quiet ERP visual comparison | PASS for scoped shell: structural reference alignment; intentional service-focused content and darker green buttons for contrast, not pixel equality |

Actual screenshots:

- [Desktop 1440](evidence/step22-20261031/health-1440.png), [1280](evidence/step22-20261031/health-1280.png), [1024](evidence/step22-20261031/health-1024.png).
- [Mobile 390](evidence/step22-20261031/health-390.png), [invalid access](evidence/step22-20261031/access-error-390.png).
- [Protected Calls](evidence/step22-20261031/protected-calls-1440.png), [verified health](evidence/step22-20261031/signed-health-1440.png).
- [Keyboard focus](evidence/step22-20261031/keyboard-focus-1440.png), [not found](evidence/step22-20261031/not-found-1440.png), [offline](evidence/step22-20261031/offline-1440.png).

UI decision: the STEP_22 foundation meets the approved visual contract within its
implemented scope. Future dashboards must retain these tokens and accessibility
behaviors and supply actual metrics; browser checks are not full WCAG certification.


## STEP_23 compatibility follow-up - 2026-10-31

The six reserved capability pages now have integrated read-only views; Settings
remains reserved. Authenticated data is gated by an API context distinguishing
synthetic fixtures from stored records. Generated contracts/standalone validation,
lazy features and a numeric loopback dev-API port override extend the shell. The
original review entry/feature/CSS and Gradio remain preserved. Shared focus styling
keeps the skip link visible only when focused. STEP_22 measurements above remain
historical; STEP_23 records its own final 27 frontend/458 backend tests and skips,
actual screenshots and limitations.
