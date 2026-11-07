# STEP_23 — Build dashboards for calls, live and model lab

**DONE — PASS WITH LIMITATIONS**, for the integrated research workspace and the
three defined step gates. Owner: Platform / Codex. Date: 2026-10-31,
Africa/Casablanca. Branch `feature/project28-foundation`; working HEAD
`a37e4634af1d2947fc3c548d54e62bda0b0daf89`; original upstream
`fed4b610742c1337147281fcec8f2cdcc0a79be5`. Windows 11, PowerShell, uv-managed
Python 3.12, Node 24.18.0 / npm 11.16.0, local PostgreSQL/Redis and Chrome.
No model inference/training, deployment, commit, push or model promotion occurred.

## 1. Goal, prerequisites and completed work

Connected the STEP_22 application shell to the existing call/report APIs and added
the minimum safe read-only projections needed for dashboard trends and model
registry inspection. Nine selected capability views now render real HTTP/database
responses: Dashboard, Calls, playback/transcript, QA/compliance, Emotion, Coaching,
Knowledge, Model lab and Live. Prototype demonstrations use synthetic records,
clearly labelled throughout; they are not operational or model-quality results.

Read the complete master instructions, STEP_INDEX, STEP_23 prompt/template,
STEP_22 report, current limitations, API/database/model contracts, design system,
acceptance checklist and both visual references before implementation. STEP_22
passes with limitations and supplies the shared shell, server identity boundary,
strict TypeScript, query lifecycle and build. Existing call/QA/report/worker
contracts satisfy the read-integration prerequisites. Production OIDC, real
browser audio transport, training/promotion and current document-search HTTP
boundaries are not available; this step shows those limits explicitly.

Built five dashboard KPIs, trends, language donut, recent calls, server filtering/
sorting/pagination, local waveform playback, keyboard slider, captions, transcript
timestamp controls, precise compliance references, QA summaries, stored action
items/policy evidence, cautious emotion shell, model provenance/registry and
authorized batch-job monitoring. Browser calling and model training remain
unavailable. Original Gradio and standalone review remain preserved.

## 2. Existing versus upgraded implementation

| Path / behavior | Original upstream at pinned SHA | Before STEP_23 | Actual STEP_23 change |
|---|---|---|---|
| `app.py`, `src/ui/app_builder.py:build_app` | Gradio entry/workflow/tabs | Existing compatible Gradio | No STEP_23 source change |
| `apps/web/src/app/App.tsx` | Absent | Six protected placeholders, health/access shell | Nine integrated capability views plus health/settings; same sidebar/topbar; lazy feature loading |
| `services/api/app.py:calls` | Absent | Scoped paginated call list | Adds validated status/language filters and whitelisted date/QA ordering; default ordering remains date descending |
| `services/api/schemas.py:CallItem`, `Report` | Absent | Call item without language; report without acoustic data/duration | Adds optional metadata; report duration from intake; acoustic signals withheld outside synthetic mode |
| `services/api/routes/workspace.py` | Absent | No activity/context/registry HTTP projections | Three new authenticated read endpoints; existing tenant/owner scope reused |
| `src/lib/api/` | Absent | Two generated DTOs, handwritten small runtime checks | Generated consumed contract closure, nested DTOs, standalone validators and scoped query helper |
| Calls/playback/citations | Gradio analysis/report baseline | No React call-detail page | Private local audio, actual waveform/native seek, unverified-source label, exact unique quote linking |
| Knowledge/coaching/emotion/model/live | No selected React workspace | Reserved pages; internal services from prior steps | Existing report evidence/metadata and explicit unavailable states; no simulated live success or automatic training |

Original Gradio entry/imports were inspected in earlier fingerprinting and remain
unchanged by this step. `git-stat-before.txt`, `git-stat-final.txt`, name-status
and full status evidence record the accumulated tree. Tracked cumulative diff is
**40 files, 1,082 insertions, 369 deletions**; most platform/frontend additions are
already untracked and do not appear in ordinary Git diff. That cumulative number
is not STEP_23's change size. `before-files.json` and `source-inventory.json`
identify scoped file hashes. No prior work/history was reset or rewritten.

## 3. File inventory and interfaces

| Created/modified file(s) | Purpose, inputs/outputs and verification |
|---|---|
| `services/api/routes/workspace.py` (new) | Context, UTC aggregate activity and admin-only registry; verified Principal/database → safe typed DTOs; integration-tested |
| `services/api/schemas.py`, `app.py`, `settings.py` | Typed projections, filters, metadata and explicit synthetic flag; preserved default API behavior/auth |
| `docs/api/openapi.json` | Regenerated actual 26-path contract, including three new GET endpoints |
| `apps/web/src/lib/api/generated.ts`, `schema.generated.json`, `validators.generated.mjs`, `validators.generated.d.mts` | Generated DTOs/schema closure/build-time compiled validators and declarations |
| `apps/web/scripts/generate-api.mjs` | Checked deterministic local-reference/type traversal and Node standalone validator compiler |
| `apps/web/src/lib/api/client.ts`, `queries.ts` | Allowed same-origin resource reads, safe errors, contract checking, cancellation and generation-scoped cache |
| `apps/web/src/app/App.tsx`, `auth.tsx`, `main.tsx`, `workspace.css` | Route wiring, transient credential access/generation, lazy features, guarded data boundary and shared styles/focus |
| `src/features/analytics/DashboardPage.tsx` | Five KPI cards, exact-count line/donut visualizations and recent calls |
| `src/features/calls/CallsPage.tsx` | Server filters, sorting, page controls, real freshness state |
| `src/features/calls/CallDetailPage.tsx` | Stored analysis/transcript, bounded native seek and unique compliance-quote timestamps |
| `src/features/calls/AudioPlayer.tsx` | WaveSurfer/native media lifecycle, local selection, keyboard slider, safe VTT captions and cleanup |
| `src/features/workspace/shared.tsx`, `features.css` | Reusable headings/loading/empty/error/status/provenance boundary, time helpers and responsive feature styles |
| `src/features/workspace/ReportWorkspace.tsx` | Selected-call QA, policy citations, action items, synthetic emotion and inference receipts |
| `src/features/live/LivePage.tsx` | Explicit no-live-transport state plus authorized job polling/pause |
| `src/features/models/ModelsPage.tsx` | Admin registry metadata and stored report provenance; no training actions |
| `apps/web/package.json`, `package-lock.json`, `.oxlintrc.json`, `tsconfig.json`, `tsconfig.workspace.json`, `vite.workspace.config.ts` | Pinned libraries, expanded lint/strict targets, generated-code lint exclusion and bounded loopback API-port override |
| `apps/web/src/app/App.test.tsx`, `src/features/workspace/workspace.test.tsx` | Updated server-contract fixtures and new behavior/seek/caption/permission/CSP checks |
| `tests/api/test_api.py`, `tests/api/test_workspace.py` | Current 26-path expectation; five new projection/PostgreSQL/signature/role/filter tests |
| `scripts/preview_workspace.py` | New loopback signed synthetic preview with separate tenant, records, silent WAV and queued fixture job; no dispatch/inference |
| `scripts/preview_emotion_reviews.py` | Existing synthetic helper explicitly labels its API data synthetic |
| `tests/frontend/dashboards.mjs` | Actual API/browser, native audio seek, responsive/axe/error checks and refresh timing evidence |
| `docs/development/dashboard-workspace.md`, this report, progress/limitations and STEP_22 compatibility note | Reproduction, precise boundaries, measured results and next-step handoff |

Frontend `src/…` paths in this table are under `apps/web/`. No source/data files
were deleted. Standalone emotion-review source/CSS, original frontend main and
review Vite config retain their pre-step hashes (`legacy-parity.json`). Their
rebuilt JS/CSS remain **232,244 / 6,708 bytes**, respectively.

## 4. Important functions, algorithms and code

`workspace_router` accepts the existing database provider and `call_query` scope.
Its authenticated context reports stored versus explicitly synthetic data and
unavailable live/training controls. `activity` restricts dates to 1–90 days, uses
UTC date grouping, fills missing dates with measured zero counts and maps missing
language metadata to Unknown. It does not infer language from audio.

```python
scoped = call_query(caller).with_only_columns(Call.id)
constraints = (
    Call.id.in_(scoped),
    Call.processed_at >= start,
    Call.processed_at < today + timedelta(days=1),
)
```

The first line retains tenant/owner authorization. The membership predicate
restricts both grouped queries to those calls. The final bounds define inclusive
UTC dates without counting future records. Returned totals differ legitimately
from all-record dashboard KPIs when older records exist; the screen states both
scopes. Model versions require admin role, tenant filter and bounded pagination;
artifact URIs/checksums/arbitrary metrics are deliberately not returned.

`calls` applies exact optional filters before counting/paging. Sort/direction are
Literal whitelists, mapped to ORM columns; unrecognized fields return 422.
Null scores sort last; ID breaks ties. No user text becomes SQL identifiers.
`Report.from_report` reuses stored summary/transcription/QA/model lineage and
projects intake duration, omitting internal audio paths. The shared report conversion withholds acoustic signals by default, including
analysis responses. Only the GET report projection explicitly enables them from
the trusted synthetic-process setting.
Real emotion exposure therefore remains disabled in the new workspace.

The generator traverses only local `#/components/schemas/…` references, handling
objects, required/optional properties, arrays, enum/const, nullable unions and
dictionary values. Unsupported/external shapes fail generation. Canonical
OpenAPI hashing and CRLF normalization make check mode reproducible. Ajv compiles
seven consumed resource validators **in Node during generation**, producing
standalone ESM functions. There is no browser schema compilation, `eval` or
Function-constructor dependency in validation. Generated compiler output is
excluded from handwritten lint, while its generation check, declarations and
behavior tests remain enforced.

```typescript
if (!Object.hasOwn(validators, name)) throw new ApiError(502);
const validate = validators[name as keyof typeof validators];
if (!validate(data)) throw new ApiError(502);
```

These three branches reject unknown contracts and invalid JSON instead of casting
bad data into success. `useApiQuery` performs the allowed same-origin read with an
abort signal and validates before caching/rendering. Query keys include the
session generation and path, never the credential. API errors take precedence
over cached display data; failed requests do not become empty/zero results.
Disconnect cancels requests and clears cache as in STEP_22.

Dashboard charts consume API counts, use explicit green/neutral colors, disable
animation and provide exact text/table equivalents. CallsPage sends filters and
sorting to the server rather than filtering one partial page. Its last-successful
query timestamp changes only after validated data completes; the browser timing
harness waits for a newly rendered timestamp, not merely an old visible count.

`AudioPlayer` accepts a user-selected local WAV/MP3, caps file bytes at 25 MB,
uses WaveSurfer with the native audio element and rejects invalid/over-30-minute
decoded duration. The waveform is decorative; native controls, a labelled range
and transcript buttons provide accessible alternatives. `safeSeek` rejects
negative/non-finite/unknown-duration inputs and clamps to duration before assigning
`audio.currentTime`. A URL `?at=` anchor seeks only once local audio is ready.
No recording identity is inferred: the screen explicitly says Source not verified.

`buildWebVtt` filters invalid/zero-after-rounding spans, rounds integer milliseconds
before splitting hours/minutes/seconds, escapes markup and creates native model
transcript captions. The 59.9999-second boundary correctly becomes 00:01:00.000.
Destroying the player stops playback, clears media source/listeners and releases
caption/object resources. WaveSurfer performs browser decoding; this is not a
streaming or hard decoded-memory isolation guarantee.

`uniqueReferenceTime` anchors only an exact quote of at least eight characters
matching one segment. Repeated, short, cross-segment or unmatched references stay
unanchored. It does not manufacture evidence timestamps with fuzzy matching.
Policy sources retain document citations separately from audio timestamps.

ReportWorkspace chooses among the latest 100 visible calls. QA displays stored
dimensions/flags; Coaching shows saved follow-up actions; Knowledge displays
supported saved citations or abstention; Emotion enforces synthetic-only exposure;
Model lab distinguishes registry metadata from inference receipts. LivePage never
claims a connected conversation: a supplied UUID polls the existing authorized
batch-job endpoint with pause control and preserves unmeasured progress as unknown.

## 5. Imports and dependency explanations

All actual versions are in `versions.json` and the npm lockfile. No backend Python
dependency was upgraded or installed for this step.

| New imports / symbols | Origin and version | Purpose / alternative / implications |
|---|---|---|
| `ResponsiveContainer`, `LineChart`, `Line`, `XAxis`, `YAxis`, `CartesianGrid`, `PieChart`, `Pie`, `Cell` | Recharts **3.10.1** | Responsive measured-count charts, explicit palette and nonanimated render. Native SVG alone would require recreating scales/layout/accessibility; raw data equivalents remain available |
| default `WaveSurfer` | wavesurfer.js **8.0.4** | Actual local waveform synchronized to native media. Native audio alone lacks a waveform; a custom canvas/audio decoder would add maintenance. No model training |
| default `Ajv2020`, default `addFormats`, default `standalone`, code-template `_` | Ajv **8.20.0**, ajv-formats **3.0.1** | Build-time JSON Schema 2020-12 compiler, UUID/date/time validation and standalone generation; browser imports only generated functions and format helpers |
| generated `fullFormats as formats`; namespace `validators` | ajv-formats helper; local generated ESM | Static format/validation functions without browser dynamic code evaluation |
| `lazy`, `Suspense`; existing `useState`, `useEffect`, `useRef`; types `ReactNode`, `RefObject`, `FormEvent` | React **19.3.1** | Feature chunk loading, local filters/media lifecycle and typed props/events; no new state-management framework |
| `Link`, `useParams`, `useSearchParams`; existing routing imports | react-router-dom **7.18.5** | Same-shell routes, UUID selection and timestamp anchors; no full-page navigation for analysis |
| `useQuery`; existing query/provider imports in tests | TanStack React Query **5.105.0** | Typed request lifecycle, cancellation, cache generation and controlled polling; avoids duplicate request-effect state machines |
| type `Dashboard`, `Activity`, `CallPage`, `Report`, `ModelVersionPage`, `JobStatus`, `WorkspaceContext`, `TranscriptionSegment` | Local generated contracts | Type-checked shapes from the actual OpenAPI closure; not unvalidated arbitrary casts |
| `useApiQuery`, `getResource`, `ApiError`, `validateResource`; shared `Heading`, `Pending`, `Empty`, `QueryProblem`, `DataBoundary`, `Status`, `safeSeek`, `timeLabel`, `uniqueReferenceTime`, `AudioPlayer`, `ReportWorkspace`; CSS imports | Local modules | Explicit presentation/request/player boundaries and reusable honest states; functions explained above |
| `Callable`, `UTC`, `datetime`, `timedelta`, `Annotated`, `cast`, `Literal`; `APIRouter`, `Depends`, `HTTPException`, `Query`, `Request`; ORM `Date`, `Select`, `func`, `select`, `Engine` | Python standard library; existing FastAPI/SQLAlchemy | Typed read-router dependency, UTC windows, validation/permissions and scoped SQL; no new infrastructure |
| Principal, Call, ModelVersion, Activity/ActivityDay/LanguageCount/ModelVersionItem/ModelVersionPage/WorkspaceContext, session_scope; EmotionResult | Local Python contracts/services | Reuses verified identity, RLS transaction and actual tables/models; projection DTOs omit sensitive storage fields |
| `os`, `json`, `time`, `Path`, `uuid4`; `jwt`, `uvicorn`, RSA/serialization, Session/create_engine/make_url; fixture report/audio/add_report, ActionItem/ComplianceFlag/TranscriptionSegment, PolicyAnswer/PolicyEvidence, ModelRun/EmotionSignal | Standard library plus existing project/test dependencies | Loopback synthetic preview with real signatures and DB fixtures. Silent audio, text, labels, scores and receipts are explicitly constructed; no inference, permissioned training corpus or human review is claimed |
| `expect`, `it`, `vi`, render/screen/waitFor, userEvent, MemoryRouter, provider/session imports; Node createRequire/fs/url/assert/performance; Chromium/AxeBuilder | Existing Vitest **5.0.5**, Testing Library, Playwright **1.64.1**, axe **4.14.0**, Node built-ins | Behavior/contract/CSP/seek tests, synthetic actual-browser capture and observed timing, with no cloud browser |

Official guidance consulted: [Recharts accessibility](https://github.com/recharts/recharts/wiki/Recharts-and-accessibility),
[WaveSurfer documentation](https://wavesurfer.xyz/docs/),
[Ajv standalone validation](https://ajv.js.org/standalone.html),
[Ajv formats](https://ajv.js.org/guide/formats.html). Existing React/Vite/TypeScript,
auth, database and model defaults remain compatible. Generated `.d.mts` files are
type declarations, not runtime validation themselves.

## 6. Concepts from first principles

A dashboard projection counts authorized stored rows; it does not make a model
more accurate. A trend groups those rows by UTC day. A language donut visualizes
the recorded metadata, with Unknown preserved when no value was saved. A fake
chart would invent values; this implementation instead uses the actual API and
marks synthetic preview data at the top of every protected view.

Generated types prevent accidental frontend/backend shape drift during development.
Standalone validators check actual JSON at runtime, after TypeScript types have
been erased. React Query distinguishes loading, success and failure; returning
an empty array from a failed request would incorrectly turn failure into success.

An evidence timestamp is a position in the selected recording. For example, the
1.25-second synthetic transcript button assigns 1.25 to native audio currentTime.
That proves seeking behavior, not that a real customer's recording or transcript
was verified. A model receipt records the model/version/prompt behind a stored
report; it does not prove registry promotion or a training improvement.

## 7. Data, security, privacy and ML boundaries

All new endpoints require the existing RS256 identity/account boundary. SQL
aggregates and lists reuse tenant/owner scope and RLS sessions; registry lookup
requires admin role. Limits/order fields are validated. No source path, S3 URI,
arbitrary model metrics or token is returned by new registry projections.

The API context explicitly labels synthetic previews. Stored-record mode describes
database rows, not certified real-call provenance. Real emotion report exposure
defaults off; only an explicitly synthetic process demonstrates signals. Existing
model-quality, data-permission/retention and production emotion NO-GO limitations
remain. There was no training, fine-tuning, hosted inference or dataset download.

Audio is selected locally and never uploaded or sent with the token. Caption
blobs are local, escaped and labelled model-generated/unverified. Playback is not
source-integrity verification; real correction workflows must establish matching
recording provenance independently. The synthetic four-second silent WAV and
fictional transcript only exercise timing/accessibility. Fixture scores, citations,
queued jobs and zero-latency model receipts are not measured model outputs.

Tokens stay in memory, queries omit cookies, requests refuse redirects, abort on
disconnect/unmount and have an eight-second bound. User text is rendered escaped,
not as executable HTML. Standalone validation avoids browser Function compilation;
this is not a claim of a fully deployed strict CSP or complete security audit.
Historical report policy passages are snapshots: current document permissions and
validity must be rechecked before reuse. No new public document-search boundary
or policy execution tool was created.

## 8. Validation, exact commands and actual results

| Command / scope | Actual result |
|---|---|
| `npm run api:check --prefix apps/web` | Exit 0; types, schema closure and standalone JS/declarations current |
| `npm run typecheck --prefix apps/web` | Exit 0; legacy strict plus stricter workspace checks |
| `npm run lint --prefix apps/web` | Exit 0; handwritten React/accessibility code, no warnings |
| `npm test --prefix apps/web` | Exit 0; **27 passed**, three files, final Vitest duration **8.65s** |
| `npm run build --prefix apps/web` | Exit 0; review and integrated workspace outputs built; wall time **3.845s** |
| `node tests/frontend/dashboards.mjs` | Exit 0; **13 compound browser assertions**, nine capability views, 17 screenshots, 16 axe audits, zero page errors/violations |
| Development smoke on `127.0.0.1:8785` → actual API `:8784` | Dashboard connects, synthetic notice visible, zero page errors |
| Scoped Ruff check/format; mypy four application/preview files | Exit 0, no errors; receipts in `static-checks.json` |
| Focused `pytest tests/api/test_workspace.py tests/api/test_api.py -q --tb=short -rs` | **42 passed**, one existing warning, 6.82s |
| Full configured backend command below | **458 passed, 2 skipped, 1 warning in 64.28s**, exit 0 |
| `npm audit --omit=dev --prefix apps/web --json` | Zero reported production vulnerabilities at check time |

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step22_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step22_test_app_url'
./.venv/Scripts/python.exe -m pytest tests/unit tests/security tests/api tests/integration tests/workers tests/llm tests/datasets tests/rag tests/emotion -q --tb=short -rs
```

The two skips are the existing pgvector knowledge tests lacking their separate
`PROJECT28_KNOWLEDGE_TEST_URL_FILE`; they are not passes. Existing pytest-asyncio
fixture-scope and Starlette/AnyIO deprecation messages remain. No remote CI run or
push is claimed; the existing frontend CI job now includes the expanded npm scripts.

Coverage includes real scoped API results, filter/order validation, admin denial,
cross-tenant registry exclusion, synthetic-mode distinction, production emotion
withholding, malformed-contract rejection, no fake success, retry/empty states,
ambiguous quote refusal, VTT escaping/minute-boundary timing, invalid seek bounds,
and validation with the global Function constructor blocked. Browser checks
exercise actual native timestamp/range seeking, four viewport widths, every
selected view, expected API fault injection/recovery, permission/empty states,
and 20 fresh validated list refreshes. This is not a full assistive-technology,
real-customer, concurrency or long-call performance certification.

## 9. Analytics, benchmarks and interpretation

**UI capability coverage:** baseline STEP_22 had placeholders, so 0/9 of the
selected integrated capability views; STEP_23 tests **9/9 (100%)** with synthetic
fixtures through the actual local API. Count includes playback/transcript and
excludes public health/access, Settings and the compliance alias. It does not
claim every future capability/backend was implemented.

**Load p95:** **36.19ms**, p50 **30.11ms**, **n=20** sequential warm-browser
calls-list refreshes over three synthetic records. Measurement starts at refresh
click and ends after HTTP 200, JSON/contract completion and a newly rendered
successful query timestamp. It includes automation overhead. Percentile formula:
sort durations, select nearest-rank `ceil(0.95*n)-1`. Baseline matched load p95:
**Not measured**. This is not cold application startup, a production SLA, inference
latency or a load/capacity benchmark; SQL/date/scale representativeness is limited.

**Accessibility:** 16 actual axe audits, zero violations across desktop/mobile
dashboard, calls, playback, selected feature/error/permission/empty screens.
STEP_22's seven zero-violation audits covered a smaller shell, so this is expanded
tested coverage, not a claim of improved WCAG conformance. Four dashboard widths
(1440/1280/1024/390) and captured mobile report/error states had zero horizontal
body overflow. Wide tables scroll within their containers.

**Build/bundle:** one final measured local build. Total emitted workspace files:
**906,665 raw bytes / 250,190 gzip bytes**, including lazy chunks,
HTML and CSS. Gzip uses Python level 9 with fixed mtime; it is not measured network
traffic. STEP_22 total was 369,055 / 111,612 bytes for a substantially smaller
foundation, so this is not an equivalent-workload regression comparison.
Main entry is **467,790 bytes / 122,044 gzip bytes**. Moving validation compilation
out of the browser reduced the earlier STEP_23 entry from 520,496 / 153,407 bytes;
no inference-speed or statistical latency improvement is inferred from that size
change. Charts/player are lazy feature chunks. Client-directive warnings from client-only dependencies remain recorded; no
threshold was raised to conceal large output. GPU VRAM, model accuracy and training metrics: **Not measured here**.

## 10. Technical questions and answers

1. **Why show a model version per report?** It makes the saved inference trace
   auditable. A receipt is separate from registry status, and neither implies
   that a newer candidate was trained or promoted by this screen.
2. **Why avoid fake production metrics?** Synthetic demonstrations are not real
   operations. The context banner labels fixtures, and live values come only
   from stored authorized records; failed requests never become invented zeros.
3. **What is an evidence timestamp?** A precise segment anchor. A unique stored
   quote can link to it; source matching and recognition accuracy still require
   verification. The native 1.25-second seek was actually executed.
4. **Why server-side filters and sorting?** Filtering one browser page would hide
   records on later pages and give incorrect totals. The server applies the same
   scoped predicates before count and pagination.
5. **Why standalone validation?** JSON must be checked after TypeScript compilation.
   Compiling in Node removes browser startup work/dynamic Function requirements
   while keeping runtime contract rejection and deterministic CI checks.
6. **Why not enable emotion analytics on customer calls?** Prior evaluation is
   insufficient for production claims. The default report route withholds signals;
   synthetic demonstrations and the existing authorized review remain explicit.
7. **What if the API is down or a user lacks permission?** The UI shows failure or
   permission-required states, offers retry/access recovery and does not show an
   empty successful registry/list. The browser exercised these branches.
8. **Why is Live not a working phone call?** Browser transport belongs to later
   steps. Showing a fabricated stream would be misleading; this route reports
   that boundary and separately monitors an authorized batch job.

## 11. Decisions, problems, fixes and remaining limits

Resolved within scope: shared report conversion now defaults to withholding
emotion data, preventing analysis responses from bypassing the synthetic guard.
Other decisions: additive safe API projections instead of parallel auth;
local playback instead of inventing an audio-storage route; exact quote anchoring
instead of guessed citations; full generated contract closure; standalone compiler
output instead of browser dynamic compilation. Browser audit found invalid ARIA
labels on generic chart wrappers; changed to labelled figures. Explicit status
control naming and asynchronous data/media waits corrected browser checks.
Caption rounding at a minute boundary and zero-millisecond spans are now tested.

Remaining limits:

- Production OIDC/PKCE/session refresh, CSP/header rollout and container packaging
  remain deployment work. The preview is synthetic and loopback-only.
- Live browser transport/calls are unavailable; fixture queued-job monitoring is
  not live speech. No training, promotion or registry mutation is exposed.
- Knowledge is a saved-report evidence view; current document search/ingestion,
  permission revalidation and policy resolution are not provided by these routes.
- Coaching is saved action items/justifications, not measured agent improvement.
  Emotion retains production NO-GO and human-review restrictions.
- Playback source identity is unverified. Byte/duration checks do not certify
  content integrity or impose a hard decoded-memory bound; WaveSurfer decodes in
  the browser, with duration rejection after decoding. Long/malformed media and
  assistive technology need further validation before production rollout.
- Report selectors/registry are bounded to the latest 100 records; calls use
  offset limits up to 10,000. Concurrent writes may shift offset pagination.
  Large transcripts, high cardinality metadata and multi-user capacity are untested.
- Two knowledge-service integration checks remain skipped. Earlier model/data/
  retention/role-attribution limitations are not resolved by this frontend.

## 12. Handoff, deliverables and evidence checklist

**Decision: PASS WITH LIMITATIONS.** All named gates passed: representative
fixture routes render; API failures do not create fake success; timestamps seek
correctly in actual native media. Next eligible: **STEP_24 — Build timestamped
human transcript and QA review**, subject to its own prompt/prerequisites.
STEP_24 was not started. Reuse the call-detail/player/query boundaries, but do not
convert unverified local audio or machine transcripts into human-approved labels
without source-provenance and reviewer safeguards.

Setup/reproduction: [workspace runbook](../development/dashboard-workspace.md).
Next safe preview command, with the explicit isolated test URL files configured:
`./.venv/Scripts/python.exe -m scripts.preview_workspace`.

- [x] Implementation, imports, concepts, actual upstream/current comparison.
- [x] Scoped file inventory, source hashes and cumulative Git diff evidence.
- [x] Executed unit/integration/browser/build/static checks and numerical analytics.
- [x] At least five answered questions and remaining boundaries recorded.
- [x] Synthetic-only screenshots; no tokens/private recordings in public artifacts.
- [x] Original Gradio/review preserved; progress and limitations updated.
- [x] No unsupported live/training/accuracy claims; next step identified only.

Evidence directory: [step23-20261031](evidence/step23-20261031/).
Key receipts: [frontend](evidence/step23-20261031/frontend-validation.json),
[backend](evidence/step23-20261031/backend-regression.txt),
[browser](evidence/step23-20261031/browser-qa.json),
[dev smoke](evidence/step23-20261031/dev-smoke.json),
[static checks](evidence/step23-20261031/static-checks.json),
[versions](evidence/step23-20261031/versions.json),
[legacy parity](evidence/step23-20261031/legacy-parity.json),
[source inventory](evidence/step23-20261031/source-inventory.json).

## 13. Approved ERP UI design / visual contract verification

Inspected `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` (primary) and
`APPROVED_GREEN_ERP_REFERENCE.png` alongside actual desktop/mobile output.
Retained the light rounded sidebar/topbar, page search/profile, spacious white
cards, charcoal hierarchy, soft-header tables, rounded controls and green palette.
The product remains Adaptive Call Center Intelligence. The reference's brand,
person, sales numbers, percentages and artificial charts were not copied.

| Contract check | Actual result |
|---|---|
| Light neutral/white cards, subtle borders, rounded sidebar/topbar | PASS, actual dashboard/report screenshots |
| Green interactions, no blue/pink brand/chart defaults | PASS; explicit Recharts palette and player colors |
| Five KPI cards, trend/language donut, recent calls | PASS; real database projections, synthetic banner on fixtures |
| Filters, sortable table, responsive layouts | PASS; 1440/1280/1024/390, body overflow zero; wide tables scroll internally |
| Accessible media and evidence | PASS tested native controls, labelled slider, model-transcript captions, actual 1.25-second seek and exact quote links |
| Loading/empty/error/retry/permission states | PASS automated component and real-browser cases |
| Keyboard/focus/reduced motion | Shared skip/main/menu behaviors retained; player keyboard seek tested; charts nonanimated; reduced-motion CSS retained |
| Contrast | Existing text #182820 / white and muted #56645D / canvas remain; axe found zero contrast violations in 16 audits |
| Shared branding and truthful copy | PASS; synthetic/unknown/unavailable states are explicit; no fabricated active call or training controls |
| Original Gradio/review behavior | Preserved source hashes/build sizes and full backend regression |

Tokens: canvas `#F6F6F3`, white `#FFFFFF`, forest `#1D5B49`, text `#182820`,
muted `#56645D`, border `#E4E8E1`, selected `#DDF2CB`. Charts use `#1D5B49`,
`#53865B`, `#9BC77B`, `#CBD8C5`, `#737E71`; waveform uses `#BBCBBD`/forest.
Amber `#805016`/`#FFF5E4` conveys synthetic/caution states. Dark green buttons
preserve readable contrast; native media controls remain browser-provided.

Actual screenshots:

- Dashboard: [1440](evidence/step23-20261031/dashboard-1440.png), [1280](evidence/step23-20261031/dashboard-1280.png), [1024](evidence/step23-20261031/dashboard-1024.png), [390](evidence/step23-20261031/dashboard-390.png).
- Calls: [table](evidence/step23-20261031/calls-1440.png), [filtered](evidence/step23-20261031/calls-filtered-1440.png).
- Transcript/player: [desktop](evidence/step23-20261031/transcript-1440.png), [mobile](evidence/step23-20261031/transcript-390.png).
- [QA](evidence/step23-20261031/qa-1440.png), [Emotion](evidence/step23-20261031/emotion-1440.png), [Coaching](evidence/step23-20261031/coaching-1440.png), [Knowledge](evidence/step23-20261031/knowledge-1440.png), [Model lab](evidence/step23-20261031/models-1440.png), [Live](evidence/step23-20261031/live-1440.png).
- [API error](evidence/step23-20261031/api-error-1440.png), [permission](evidence/step23-20261031/permission-1440.png), [empty mobile](evidence/step23-20261031/empty-390.png).

Intentional differences: synthetic banner, evidence/status-oriented content, no
sales comparisons, no imaginary live/HR/training analytics, read-only registry,
local unverified audio selection and darker accessible primary buttons. UI review
passes this scoped contract; it is not pixel equality or a complete WCAG audit.
