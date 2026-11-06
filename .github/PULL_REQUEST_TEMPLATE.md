## Outcome and scope

Describe the concrete problem, resulting behavior and compatibility impact.

- Project 28 step / issue:
- Important changed files and rationale:
- Ownership: AI/ML / Platform / shared
- Other developer requested as reviewer (actual account, not an assumed identity):

## Tests and acceptance evidence

Record exact commands, environment, exit codes, pass/fail/skip counts and local
evidence paths. Label unexecuted checks and explain why. Do not paste secrets.

| Check | Command / environment | Actual result | Evidence |
|---|---|---|---|
| Regression / integration | | | |
| Lint / format / typing | | | |
| Step acceptance criteria | | | |

- Known failing checks: baseline comparison, impact, owner and follow-up.
- [ ] Relevant current behavior and negative cases are covered; no unexplained regression.
- [ ] A failing check is not represented as passed or hidden by an ignore/skip.

## Security and data

- Data/permissions/authentication/PII impact and regression checks, or reason not applicable:
- [ ] No keys, private recordings, raw sensitive transcripts or unsafe log attachments.
- [ ] No security check was weakened to make validation pass.
- [ ] Dataset use/training permissions verified if data or models change.

## Documentation and compatibility

- Step report path and affected architecture/API/setup documentation:
- Migration, rollback and recovery impact, or reason not applicable:
- [ ] Report and measured metrics match current source and execution evidence.
- [ ] Original behavior, attribution and MIT notice are preserved where required.

## ML evidence (if applicable)

Model/checkpoint and dataset versions, split/leakage checks, sample counts,
baseline/candidate metrics, hardware and reproducible evaluation command:

State whether training actually ran. Promotion/rollback approval is separate;
an annotation interface or configuration change is not proof of learning.

## UI evidence (if applicable)

Actual before/after desktop/mobile screenshots, comparison against
`design/APPROVED_COMMMERCIALLY_STYLE_REFERENCE.png`, color tokens, interaction and
accessibility results. Explain deviations. Never reuse mock reference metrics.
For non-UI changes, state why visual verification is not applicable.

## Review and merge

- Related issues / limitations:
- [ ] Followed [Project 28 workflow](../docs/development/workflow.md).
- [ ] Cohesive milestone commits use Conventional Commits; no invented elapsed history.
- [ ] Other developer reviewed the current revision; discussions resolved and checks recorded.
- [ ] No push, merge, deployment or published-history rewrite beyond explicit authorization.
