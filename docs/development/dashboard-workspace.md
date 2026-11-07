# Dashboard and call-analysis workspace

STEP_23 extends the shared `/workspace/` SPA. Overview, Calls, QA/compliance,
Emotion review, Coaching, Knowledge, Model lab and Live monitoring share one shell.
`/workspace/#/calls/<UUID>` opens playback/transcript and compliance evidence.
`/workspace/#/compliance` is an alias of the QA/compliance view.

## Run locally

```powershell
npm ci --prefix apps/web
npm run api:check --prefix apps/web
npm run build --prefix apps/web
```

Restart your configured FastAPI process after code/build changes. Production
identities still require the existing issuer/audience/key or JWKS configuration
and enabled tenant accounts. The UI stores short-lived access only in tab memory.
No guest authorization, production login provider or training permission is added.

For an explicitly synthetic preview, set the private URL-file variables to an
isolated migrated test database and its restricted runtime role:

```powershell
$env:PROJECT28_TEST_ADMIN_URL_FILE='.local/step22_test_admin_url'
$env:PROJECT28_TEST_APP_URL_FILE='.local/step22_test_app_url'
./.venv/Scripts/python.exe -m scripts.preview_workspace
```

This helper refuses unmatched/non-test/non-loopback databases, creates a new
synthetic tenant, stores ephemeral signed test credentials under ignored
`.local/step23-ui-context.json`, and serves the actual API/build on port 8784.
It does not run inference, dispatch the fixture job, train or create human labels.
Open `http://127.0.0.1:8784/workspace/`. Keep test credentials private.
Existing review UI and Gradio remain separate; no production container is replaced.

For development against that preview, in another PowerShell session:

```powershell
$env:PROJECT28_DEV_API_PORT='8784'
npm run dev --prefix apps/web -- --port 8785
```

The dev API target is always loopback; only its numeric port is configurable.
Without that variable it retains port 8781. Do not use an old API process with
the new build: the new context/activity/registry routes require restarting updated
source. The original review development entry remains `npm run dev:review`.

## Screens and boundaries

- Overview: five server-derived totals, a 30-UTC-date trend, recorded language
  distribution, and five recent visible calls. Unknown metadata stays Unknown.
- Calls: server-side exact status/language filters, date/score sorting and offset
  pagination. QA is on the actual 1–5 scale; no invented percentages or duration.
- Call analysis: recorded summary, QA, transcript and flags. Choose corresponding
  WAV/MP3 locally, up to 25 MB / 30 minutes. Nothing is uploaded. Source identity
  is explicitly unverified. WaveSurfer draws the waveform; native controls,
  keyboard seek slider, model-transcript captions and timestamp buttons work.
- QA/coaching/knowledge: choose among the latest 100 visible calls. Inspect
  existing scores, follow-up items and report policy citations. No company-wide
  document HTTP ingestion/search, new coaching model or current-policy validation
  is implied. Ambiguous transcript references do not get guessed timestamps.
- Emotion: production report exposure is disabled. Synthetic preview signals are
  labelled uncertain/uncalibrated. Existing authorized human correction remains
  under `/review-ui/`.
- Model lab: admin-only tenant registry metadata plus report inference receipts.
  No artifact locations, training controls or promotion actions are exposed.
- Live: explicitly unavailable browser-call transport; optionally monitor a real
  authorized batch-job ID. The synthetic fixture job stays queued and is not a
  streaming conversation. Polling can be paused.

## Verification

```powershell
npm run lint --prefix apps/web
npm run typecheck --prefix apps/web
npm test --prefix apps/web
node tests/frontend/dashboards.mjs
```

The browser script requires the running synthetic preview and Chrome at its
standard Windows location. It captures only synthetic fixtures. It checks real
HTTP/database results, errors, empty/denied states, actual native audio seeking,
four viewport widths, axe, and 20 sequential fresh call-list refresh timings.
Evidence is saved in `docs/implementation/evidence/step23-20261031/`.

After intentional API schema changes, regenerate `docs/api/openapi.json` from
`create_app(ApiSettings()).openapi()`, then run `npm run api:generate --prefix apps/web`.
The generator creates TypeScript types, a consumed-schema closure and standalone
JavaScript validators in Node. No schema compilation or Function constructor is
needed in the browser. `api:check` verifies all generated outputs without writing.
Generated compiler output is excluded from handwritten lint; behavior and contract
checks validate it. Do not edit generated files manually.
