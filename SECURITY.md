# Security Policy

## Supported Versions

This project is currently distributed as a single rolling release on the `main` branch. Security fixes are applied to `main` and, where applicable, picked into the version pinned by the HuggingFace Space.

| Version | Supported |
|---|---|
| `main` (latest commit) | Yes |
| Older tagged releases | Best effort only |

If you are deploying the project, pin to a specific commit SHA and watch for updates.

## Reporting a Vulnerability

**Please do not file a public GitHub issue for security vulnerabilities.** Public disclosure before a fix is available puts users at risk.

To report a vulnerability privately, use one of the following channels:

1. **GitHub Private Vulnerability Reporting** (preferred). Go to the `Security` tab of this repository and choose `Report a vulnerability`. The submission is visible only to the maintainer.
2. **Email.** Send a description to the maintainer's GitHub-attached email. Include:
   - A clear description of the vulnerability and the impact.
   - A minimal reproduction (steps, payload, or proof-of-concept).
   - Your name and how you would like to be credited (or anonymous).

You should receive an acknowledgment within 72 hours. A triage decision (accepted, needs more info, declined) follows within 7 days.

## What to Expect

If the report is accepted:

- The maintainer will work on a fix and keep you updated.
- We will agree on a coordinated disclosure timeline. The default is 90 days from acknowledgment, shortened if a fix is ready earlier.
- You will be credited in the release notes unless you prefer to remain anonymous.

If the report is declined:

- The maintainer will explain why (for example, the behavior is by design, or the threat model does not apply).
- You are welcome to file a public issue at that point if you disagree, but please keep the discussion respectful.

## Known Risk Areas

These are documented for transparency.

### Prompt-injection patterns are best-effort

The transcript is checked against 22 known prompt-injection patterns at `src/security/injection_detector.py:6-29`. The regex set catches direct attempts but is bypassable with character substitution, synonyms, or whitespace tricks. The README's claim of "blocked" should be read as "checked against known patterns". If your threat model requires stronger guarantees, add a learned classifier upstream of the LLM call.

### PII redaction misses unseparated SSN strings

The SSN pattern at `src/security/pii_redactor.py:23` requires a `-` or whitespace separator between digit groups. A nine-digit string with no separator is not redacted. Consider adding a second pattern matching standalone 9-digit tokens. There is a small false-positive risk (any nine-digit reference number gets redacted), which is the right trade-off for call-center transcripts.

### SQLCipher PRAGMA is built with an f-string

The PRAGMA key is interpolated directly into the SQL string at `src/database/connection.py:29`. Exploitation requires control of the `DB_ENCRYPTION_KEY` environment variable, which is also what controls the database encryption itself, so the practical impact is low. The recommended mitigation is to escape embedded single quotes in the key before interpolation, or to constrain the key to hexadecimal characters at config-load time.

### Audit log can persist arbitrary dict content

The audit log accepts a `details: dict | None` parameter at `src/security/audit.py:23-32`. Today every caller passes safe content, but if a future code path passes PII (for example, the raw transcript), the log becomes a leak vector. The Observability tab truncates to 60 characters, but the persisted column is unbounded. Pass user-supplied dicts through `src/security/pii_redactor.py` before logging.

### No authentication on the Gradio UI

The Gradio app exposes the UI without authentication. This is acceptable for a private HuggingFace Space or a localhost deployment. For any public deployment, place the app behind an authenticated reverse proxy.

## Out of Scope

The following are explicitly out of scope for this security policy:

- Vulnerabilities in third-party dependencies that are already fixed in newer versions. Bump the dependency and open a regular PR.
- LLM behavior issues (hallucinations, refusals, biased output). These are model-level concerns, not application security.
- Denial-of-service attacks against the local Gradio server. The mitigation is to deploy behind a rate-limiter.
- Attacks that require physical access to the host or the user's browser.

## Hall of Fame

Researchers who have responsibly disclosed valid security issues will be listed here with their permission.

(no reports to date)
