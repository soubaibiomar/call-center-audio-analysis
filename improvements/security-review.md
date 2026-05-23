# Security Review

Advisory security audit of the Call Center Intelligence System. This report covers the threat model, the existing defenses, and the findings ordered by severity.

## Threat Model

The system accepts user-supplied audio files, transcribes them, sends the transcript to a third-party LLM, and persists structured results to a local SQLite database. The trust boundaries are therefore:

1. **Audio file upload** at `src/services/pipeline.py:49-89`. The bytes are entirely user-controlled.
2. **Transcript text** at `src/agents/transcription.py:200-292`. After Whisper transcribes the audio, the text is again user-controlled (Whisper outputs whatever it hears).
3. **LLM call** at `src/agents/summarization.py:62-74` and `src/agents/qa_scoring.py:146-158`. The transcript is sent to a remote API.
4. **Database write** at `src/agents/report.py:41-66`. Persisted fields include the (PII-redacted) transcript and JSON-serialized model outputs.

The existing defenses are encouraging:

- A prompt-injection scan runs **before** any LLM call (`src/security/injection_detector.py`).
- PII redaction runs **after** the injection scan and **before** any LLM call (`src/security/pii_redactor.py`).
- The audit log is append-only and uses dedicated columns rather than a free-text blob (`src/database/models.py:28-36`).
- Temp-file cleanup is rolling (`src/services/pipeline.py:23-33`).
- The `.env.example` documents every secret and ships placeholder values (`.env.example:1-31`).
- The `.pre-commit-config.yaml` runs `detect-secrets` on every commit (`.pre-commit-config.yaml:9-13`).

## Findings

### SEC-01 - Unsafe PRAGMA construction with f-string {#sec-01}

- **Severity:** Medium
- **Exploitability:** Low (requires control of `DB_ENCRYPTION_KEY` env var)
- **Effort to fix:** Small (under 30 minutes)
- **File:** `src/database/connection.py:23-33`

```python
# src/database/connection.py:23-33
if encryption_key and os.environ.get("DB_ENCRYPTION_KEY"):
    try:

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute(f"PRAGMA key='{encryption_key}'")
            cursor.close()

    except Exception:
        pass  # Fall back to unencrypted SQLite
```

The PRAGMA statement is built by string interpolation. If `DB_ENCRYPTION_KEY` contains a single quote or a semicolon, the statement either fails to parse or executes additional SQL. In practice this is a configuration injection rather than a remote attack: only someone who already controls the host's environment variables can exploit it. However, this is also a defense-in-depth gap, because the developer-friendly auto-key in `src/utils/config.py:14` is `secrets.token_hex(16)`, which would never contain a special character, while a human-typed key easily could.

**Recommended fix.** SQLite PRAGMA statements do not accept parameters in the usual `?` placeholder form, but you can quote the value safely by replacing each single quote in the key with two single quotes:

```python
safe = encryption_key.replace("'", "''")
cursor.execute(f"PRAGMA key='{safe}'")
```

Or, more robustly, reject keys that contain anything other than hexadecimal characters at config-load time. The hex constraint matches the `.env.example:18` placeholder (`your-32-byte-hex-key-here`) and makes the PRAGMA safe by construction.

A patch is provided under `improvements/patches/SEC-01-parameterize-pragma-key.patch`.

### SEC-02 - PII redactor misses unseparated SSN {#sec-02}

- **Severity:** Medium
- **Exploitability:** Medium (a real call where the customer reads their SSN as "one two three four five six seven eight nine" would be transcribed as that or as the digit string `123456789` and would not be redacted)
- **Effort to fix:** Small (under 15 minutes)
- **File:** `src/security/pii_redactor.py:22-31`

```python
PII_PATTERNS: list[tuple[str, str, str]] = [
    (r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b", "SSN", "[REDACTED_SSN]"),
    ...
]
```

The SSN pattern requires either a dash or a whitespace between the three digit groups. An SSN spoken as "one two three, four five, six seven eight nine" is likely to be transcribed without separators as `123456789` or `123 45 6789`. Neither matches.

The credit-card pattern is more forgiving (it accepts no-separator), but the SSN pattern is tighter than it should be.

**Recommended fix.** Add a no-separator SSN pattern as a second entry. Anchor it on word boundaries to avoid eating regular ten-digit phone numbers:

```python
(r"\b\d{9}\b(?=\s|$|[^\d-])", "SSN", "[REDACTED_SSN]"),
```

There is a small false-positive risk (any nine-digit standalone number gets redacted). For call-center transcripts that is the right trade-off: a leaked SSN is a far worse outcome than a redacted reference number.

### SEC-03 - Prompt-injection patterns are easily bypassed {#sec-03}

- **Severity:** Medium
- **Exploitability:** Medium (anyone whose voice gets transcribed can attempt to bypass)
- **Effort to fix:** Small (one to two hours)
- **File:** `src/security/injection_detector.py:6-29`

The injection detector compares the transcript against 22 case-insensitive regex patterns. The patterns cover well-known attacks (`ignore previous instructions`, `<<SYS>>`, `[INST]`, `DAN mode`, social engineering, prompt-leak questions). They will catch direct attempts.

They are bypassable in at least three obvious ways:

1. **Punctuation insertion.** "Ignore. all. previous. instructions" does not match the pattern `ignore\s+(all\s+)?previous\s+instructions`, which only allows whitespace between the words.
2. **Synonyms.** "Disregard your earlier directives" matches none of the patterns (`disregard prior instructions` is covered, `earlier directives` is not).
3. **Whisper transcription artifacts.** Whisper does not always preserve punctuation or word boundaries, which can both fail to match a real attack AND match an innocuous transcription as suspicious.

**Recommended fix (small).** Normalize the transcript before matching: lowercase, collapse whitespace, strip punctuation, then run the patterns. Add a length cap so a hostile transcript cannot trigger catastrophic backtracking.

**Recommended fix (medium).** Replace the regex set with a small LLM classifier or a hash-based blocklist that you can update over time. The current approach is acceptable as a first line of defense **provided** the README's claim that injection is "blocked" is qualified as best-effort.

The README's claim at `README.md:60` ("PII redacted before any LLM call; 22 prompt-injection patterns blocked at ingestion") slightly oversells the protection. Consider rewording to "checked against 22 known patterns".

### SEC-04 - Auto-generated DB encryption key is dead code that suggests stronger behavior {#sec-04}

- **Severity:** Low
- **Effort to fix:** Small (under 15 minutes)
- **File:** `src/utils/config.py:12-14`

Detailed in `code-review.md#cr-04`. Recapping: the `_DEFAULT_DB_KEY = secrets.token_hex(16)` is generated on import but is never actually applied to SQLCipher because the activation check at `src/database/connection.py:23` requires the `DB_ENCRYPTION_KEY` environment variable to be present. The result is that the database is unencrypted by default, but a casual code reader could believe it is.

### SEC-05 - Pre-commit secret regex is permissive {#sec-05}

- **Severity:** Low
- **Effort to fix:** Small (under 15 minutes)
- **File:** `.pre-commit-config.yaml:15-21`

```yaml
- id: no-secrets-in-code
  name: Check for hardcoded API keys
  entry: bash -c 'grep -rn "sk-[a-zA-Z0-9]" --include="*.py" src/ && exit 1 || exit 0'
  language: system
  pass_filenames: false
```

The pattern matches any string starting with `sk-` followed by a single alphanumeric character. That catches OpenAI-style keys, but it also matches innocuous strings such as `sk-...` placeholders in comments and any test string of the form `sk-1`. Worse, it does not look outside `src/`, so a key committed to `tests/`, `data/`, or the repo root is invisible to the hook.

Note that the `detect-secrets` hook above is a much stronger check. The custom hook is redundant and risks giving a false sense of coverage.

**Recommended fix.** Either delete the local hook (let `detect-secrets` do the job) or tighten the pattern to require a minimum length (`sk-[A-Za-z0-9]{20,}`) and scan the entire repository.

### SEC-06 - Audit log details column accepts arbitrary JSON {#sec-06}

- **Severity:** Low
- **Effort to fix:** Small (under 30 minutes)
- **File:** `src/security/audit.py:23-32`

```python
def log(self, call_id: str, action: str, user: str, details: dict | None = None) -> None:
    with session_scope(self.engine) as session:
        entry = AuditLogEntry(
            ...
            details=json.dumps(details) if details else None,
        )
```

Callers pass arbitrary dicts as `details`. Today every call site (`src/services/pipeline.py:119, 134`) passes safe data, but future code paths could include PII that the database persistence layer has no way to filter. If the audit log itself is ever exposed (for example, in the Observability tab at `src/services/observability.py:93-103`), this becomes a leak vector.

The Observability tab already truncates to 60 characters at `src/services/observability.py:100`, which is good. But the persisted column is unbounded.

**Recommended fix.** Add a `redact_pii` pass over `details` before serializing. The function already exists at `src/security/pii_redactor.py:34-71`.

### SEC-07 - No CSRF or rate limiting on the Gradio app {#sec-07}

- **Severity:** Low (depends on deployment)
- **Effort to fix:** Medium
- **File:** N/A (deployment concern)

Gradio's default deployment exposes the application without authentication. For a HuggingFace Space, this is by design; for any other deployment, the app accepts unauthenticated uploads of up to 50 MB (`src/utils/audio.py:13`).

**Recommended fix.** If you deploy this anywhere other than a private HF Space, put it behind an authenticated proxy (Caddy with basic auth, Cloudflare Access, or an nginx reverse proxy with rate limiting). The `Dockerfile` added by this audit can be paired with such a proxy.

### SEC-08 - Secrets scan of the existing repository {#sec-08}

A full filesystem scan of the audit checkout found **no** committed secrets. Patterns searched: `sk-[A-Za-z0-9]{20,}`, `AKIA[0-9A-Z]{16}`, `ghp_[A-Za-z0-9]{20,}`, `xoxb-`, `xoxp-`, `-----BEGIN .* PRIVATE KEY-----`.

The `.env.example` correctly uses placeholders (`your-openai-api-key-here`).

## Strengths Worth Preserving

- **Defense in depth.** Two security layers (injection detection then PII redaction) before any LLM call is the right architecture.
- **Audit log.** Append-only by design, with `call_id` and `timestamp` indexed.
- **Temp-file lifecycle.** `_cleanup_old_temp_files` at `src/services/pipeline.py:23-33` is a small but important touch.
- **`.gitignore` rules.** Already exclude `.env`, IDE files, `.streamlit/secrets.toml` (wisely listed despite no Streamlit usage), and the `.claude/` working directory.
- **Pinned dependencies.** `requirements.txt` uses `==` for every package, which prevents supply-chain surprises (see `dependencies.md#dep-01` for the trade-off discussion).
