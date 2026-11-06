# Project 28 development workflow

This is the working agreement for the two project developers. It supplements
[CONTRIBUTING.md](../../CONTRIBUTING.md), the master instructions and each step's
acceptance criteria. It defines local conventions; it does **not** enable GitHub
branch protection, install hooks, assign human accounts or publish labels by itself.

The current development branch `feature/project28-foundation` already exists and
is reused. `main` and `upstream/main` remain at the pinned original
`fed4b610742c1337147281fcec8f2cdcc0a79be5`; `origin/main` and working HEAD are at
the preparation commit `a37e4634af1d2947fc3c548d54e62bda0b0daf89`. These are the
STEP_03 starting snapshots, not a promise that remote branches never advance.
`origin` is the user's fork; `upstream` is ANI-IN's original repository. PR base
`main` means the **fork's** main, not permission to push to the original repository.

## Collaboration rules

### W01 — Preserve the original baseline and existing work

Keep the STEP_02 full clean sibling clone and its recorded SHA for comparisons.
Never reset, clean, delete or overwrite existing work to make a check green. Before
integration inspect `git status --short`, `git diff` and the intended refs. Do not
work directly on `main`, rewrite published history or alter existing Ollama services.
Git branches alone do not enforce these policies; remote settings are separate.

### W02 — Reuse branches safely and name new work predictably

Use the existing development branch for the authorized in-progress work. Only
create a requested development branch if it does not already exist; never reset
an existing branch to a new base. Future scoped branches use
`<type>/step-<NN>-<short-kebab-description>`, with `feat`, `fix`, `docs`, `chore`,
`refactor`, `test`, `ci`, `build` or `perf`. For example,
`feat/step-09-call-api` is a naming example, not a branch created by STEP_03.
The existing `feature/` prefix is retained for compatibility. Keep branches focused
and integrate at reviewable outcomes; do not split commits merely by elapsed minutes.

### W03 — Assign responsibility by actual component

| Surface | Primary responsibility | Required peer input |
|---|---|---|
| `src/agents/`, model inference/evaluation, datasets, training | Developer 1 — AI/ML | Developer 2 reviews integration, data handling and operations |
| `src/database/`, `src/services/`, `src/ui/`, `.github/`, deployment/configuration | Developer 2 — Platform | Developer 1 reviews analysis behavior and ML contract impact |
| `src/graph/`, `src/security/`, shared schemas, privacy and model promotion | Shared; name an author/owner in the PR | Both responsibilities reviewed; the author cannot supply the independent approval |
| `tests/` and `docs/` | Owner of the behavior being tested/documented | Other developer checks evidence and reproducibility |

These are roles, not invented GitHub identities. Record actual author/reviewer
accounts when opening a PR. No CODEOWNERS file is installed until valid collaborating
accounts/teams and permissions are known; the ownership table is the local agreement.

### W04 — Review the current revision independently

Use the [PR template](../../.github/PULL_REQUEST_TEMPLATE.md). The other developer
reviews the current revision for acceptance, original behavior, tests, security,
cost and complexity. Address discussions and obtain one independent approval before
merge. Material fixes, conflict resolutions or amended content invalidate prior
validation/approval as applicable: rerun affected checks and request review again.
An AI status or an author's self-review is not the required human peer approval.
No peer approval is claimed by a local step execution report.

### W05 — Attach executable acceptance evidence

State the step, changed files, exact commands/environment, exit codes, pass/fail/skip
counts, observed metrics, limitations and durable report paths. Use synthetic or
consented fixtures. From the existing uv-managed Windows environment:

```powershell
.venv/Scripts/python.exe -m pytest tests/ -q --tb=short
.venv/Scripts/python.exe -m ruff check src/ tests/ app.py
.venv/Scripts/python.exe -m ruff format --check src/ tests/ app.py
.venv/Scripts/python.exe -m mypy src/
git diff --check
```

Run focused checks for changed development scripts too. Full-project mypy currently
fails as documented in STEP_01/STEP_02; report the actual failure and precise baseline
comparison. A scoped type pass does not make the full check pass. Do not install
heavy runtime dependencies, add ignores or skip failing cases solely to claim green.
Package/setup work belongs to its authorized step; use uv, not Conda.

### W06 — Resolve conflicts without losing unrelated changes

Coordinate who edits shared files before integration. Inspect dirty work first;
do not automatically stash, reset, clean or switch away from it. Establish a clean
reviewable checkpoint only with the necessary commit authorization, or an explicitly
agreed isolated workspace. After fetching/integrating when authorized, inspect each
conflict against both intents and the pinned original. Resolve deliberately, rerun
affected tests plus relevant regressions, update the report and obtain fresh review.
If resolution is uncertain, preserve the conflict evidence and ask the other owner.
Do not accept all of one side or force-push as a generic conflict workaround.

### W07 — Make cohesive milestone commits with truthful dates

Use Conventional Commit subjects, for example
`docs(collaboration): establish project review and evidence conventions`, with a
body explaining scope, rationale and material validation. Group implementation,
configuration, documentation and verification when they form one logical outcome.
Avoid a commit for every edit or a minute-by-minute schedule. Commit/push only when
authorized; this document is not that authorization.

The user prefers adjusted commit dates spanning days even when work takes hours.
Before applying any adjusted timestamp, establish the exact intended dates and
timezone with the user; do not invent a schedule or claim actual elapsed engineering
time. Do not delay execution to simulate days. Changing existing published history
or force-pushing needs separate explicit authorization. Prefer preserved history;
squash only the agreed unpublished PR changes when the merge is authorized, never
silently discard original attribution or previously published history.

### W08 — Meet merge requirements and distinguish policy from enforcement

Merge only with the other developer's current approval, resolved discussions,
passing step acceptance criteria, current relevant test/security/docs evidence,
no new unexplained regressions and an identified rollback/migration impact. An
existing failing check requires exact baseline evidence, impact/owner/follow-up and
an explicit reviewer decision; it is not a blanket exemption. FAIL steps do not merge.
No deployment or model promotion follows automatically from a PR merge.

For the fork's main branch, the intended server policy is PR-only integration,
one independent approving review, re-review after material changes, resolution of
discussions, and required relevant CI checks; disallow force pushes/deletion and
restrict bypasses. An authorized repository administrator must inspect and activate
appropriate hosting rules and confirm the actual reported check names. GitHub
protection status has **not been inspected or changed** by STEP_03. The existing
`CI` workflow checks lint/format/compile/unit/security; its dependency audit is
advisory. Neither that job nor this document proves all security/typing gates pass.

### W09 — Keep collaboration evidence safe

Never commit keys, ignored `.env`, private recordings, raw sensitive transcripts or
customer identifiers into issues, PR bodies or screenshots. Share sanitized logs
and synthetic reproductions. Follow [SECURITY.md](../../SECURITY.md) for private
security disclosure. A label `area:security` is for safe engineering coordination,
not permission to publish a sensitive finding. Retain MIT attribution and verify
recording/dataset rights separately; code license is not audio-training consent.

### W10 — Review ML claims and model changes with lineage

AI/ML changes identify checkpoint/processor versions, dataset version and permissions,
split/leakage controls, sample counts, hardware, baseline/candidate metrics and the
reproducible evaluation command. Report whether gradient-based training actually ran.
Do not substitute a heuristic, annotation UI or fabricated metric for a neural
improvement. Respect 8 GB VRAM, separate training from production inference and
require explicit promotion/rollback approval after the relevant measured gates.
For non-ML work, state that inference/training metrics are not measured.

### W11 — Review frontend changes against the approved reference

Frontend changes use `design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png` and the
design system/checklist: neutral canvas, white rounded cards, green accents, dark
text, responsive behavior and accessible controls. Attach actual before/after
desktop/mobile screenshots plus tokens, interaction/accessibility results and
explained deviations. Preserve original Gradio until tested parity. Non-UI steps
state why screenshots are not applicable; mock reference values are never metrics.

### W12 — Use a local label catalog without claiming remote state

[`.github/labels.json`](../../.github/labels.json) defines names, six-digit RGB
colors (no `#`) and descriptions. `bug` and `enhancement` remain compatible with
the existing issue templates. Add `documentation`, an `area:*`, a priority and
`status:*` when useful; labels classify work rather than grant access or approval.
P0 is critical, P1 high, P2 medium and P3 low. `status:blocked` requires a concrete
dependency/next action; `status:needs-review` requests the other developer's review.

The catalog is local source configuration. It does not provision GitHub labels.
Applying it later requires an authorized administrator to compare existing labels,
create/update only approved entries, preserve unrelated labels and verify results.
No remote label write, automatic deletion, PR creation or push occurs in STEP_03.
Unreviewed remote PR count is **Not measured**, not zero; no remote inventory was queried.
