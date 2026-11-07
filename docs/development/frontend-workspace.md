# Frontend workspace

STEP_22 adds the application foundation at `/workspace/`. The existing standalone
emotion review remains at `/review-ui/`; Gradio remains available separately.
Overview, Calls, Live monitoring, Knowledge base, Model lab and Settings are
authenticated route placeholders. They do not yet load their feature data.

## Local development

Use Node 24.18.0 and the checked-in npm lockfile. From the repository root:

```powershell
npm ci --prefix apps/web
npm run dev --prefix apps/web
```

Open `http://127.0.0.1:8783/workspace/`. The loopback-only development server
forwards `/api`, `/health` and `/ready` to the local API on port 8781. Start your
configured API separately, for example:

```powershell
./.venv/Scripts/python.exe -m uvicorn services.api.app:create_app --factory --host 127.0.0.1 --port 8781
```

Default API settings fail closed. `/health` may succeed while `/ready` or protected
access is unavailable. An administrator must configure the existing OIDC issuer,
audience and verification key/JWKS and enable the tenant account. The frontend
accepts an existing short-lived bearer token; it does not issue tokens or implement
an OIDC authorization-code/PKCE login. Never configure tokens in `VITE_*` variables.
Only a nonproduction synthetic preview should use the test identity helper.

The access field clears on submission. Tokens remain only in tab memory, are not
part of query keys or URLs, and disappear on reload/disconnect. The server verifies
the identity at `/api/v1/me`; the browser's route guard is not the security boundary.
Identity is rechecked on focus/reconnect and every 60 seconds while connected.
Disconnect cancels pending queries and clears the query cache.

## Build, serve and contracts

```powershell
npm run api:check --prefix apps/web
npm run lint --prefix apps/web
npm test --prefix apps/web
npm run build --prefix apps/web
```

`dist/` contains the original review build; `dist-workspace/` contains the new shell.
FastAPI mounts each only when its directory exists at application creation. Restart
the API after building for the first time. The workspace uses hash routes, such as
`/workspace/#/calls`, so static hosting requires no catch-all API rewrite. No Node
server is needed to serve built files. Docker's current backend image does not
automatically bundle these frontend outputs; container packaging is separate work.

`npm run dev:review --prefix apps/web` preserves the old review development entry.
When the API schema changes, regenerate its reviewed OpenAPI snapshot and run
`npm run api:generate --prefix apps/web`. The narrow generator supports the
Health/Identity string and enum fields consumed here and rejects unsupported
schema shapes. CI checks a canonical schema hash and generated output; runtime
validation separately rejects malformed JSON or unexpected identity roles.

## Browser validation with synthetic identities

Point `PROJECT28_TEST_ADMIN_URL_FILE` and `PROJECT28_TEST_APP_URL_FILE` at private
URL files for an explicitly isolated test database with current migrations and a
restricted runtime role. Do not use the production database. Then:

```powershell
./.venv/Scripts/python.exe -m scripts.preview_emotion_reviews
# In another PowerShell session, after building:
node tests/frontend/workspace.mjs
```

The preview checks for a test database, seeds synthetic records/accounts, listens
on 127.0.0.1:8781 and writes ephemeral signed tokens to ignored storage. The browser
harness reads them privately, captures no token values and supports only loopback
ports 8781/8783. Chrome at the standard Windows path is required locally; it can
use Playwright's Chromium on other systems after explicit installation.

To rerun the existing review harness without replacing STEP_21's historical proof:

```powershell
$env:PROJECT28_REVIEW_EVIDENCE_DIR='docs/implementation/evidence/step22-20261031/legacy-review'
node apps/web/tests/emotion-review.mjs
```

STEP_22 tests used dedicated databases recorded in its report and a separate Redis
container on 127.0.0.1:16379 for the existing worker regression suite. They did not
repair or reconfigure the existing Compose Redis service. No model inference or
training is needed for these frontend checks.
