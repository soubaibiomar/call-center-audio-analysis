# Accessibility and UX

Advisory review of the Gradio UI under `src/ui/`. This system has a real user interface, so accessibility and usability matter. The findings below are all small wins; nothing is broken.

## Snapshot

The UI is a 3-tab Gradio Blocks app:

1. **Analyze Call** (`src/ui/tabs/analyze.py:14-110`) - upload or record audio, view transcript, summary, and QA scores, download PDF / JSON.
2. **All MP3 History** (`src/ui/tabs/history.py:32-185`) - master-detail table over past calls.
3. **Observability** (`src/ui/tabs/observability.py:10-39`) - metrics dashboard and audit trail.

All three tabs share a soft theme (`src/ui/app_builder.py:20`). The architecture is sound: presentation is split from services, autoload wiring is explicit, and the master-detail flow is correctly implemented.

## UX-01: Long-running pipeline has good but coarse feedback

- **Severity:** Low
- **Effort:** Small
- **File:** `src/ui/tabs/analyze.py:63-74`

The "Processing your call..." banner is shown at click time and remains until the pipeline finishes. For a 10-minute call this is 5 to 10 minutes of "please wait" with no progress signal. Users tend to refresh.

**Suggested improvement.** Surface staged progress (intake done, transcription done, redaction done, scoring done) via a `gr.Progress` or a streaming `yield` from the pipeline. The LangGraph workflow already passes through each node, so the hooks are there.

## UX-02: Error banner does not distinguish failure modes

- **Severity:** Low
- **Effort:** Small
- **File:** `src/ui/tabs/analyze.py:75-88`

Every failure renders as `Pipeline failed\n\n<error_text>`. That covers the three real cases (validation, injection, LLM failure) with a single banner. A user who uploaded a 51 MB file gets the same red box as a user whose OpenAI key expired.

**Suggested improvement.** Use the existing `status` value (`failed` vs `flagged_for_review`) to choose a different color and title. `gr.Warning` for review-flagged calls, `gr.Error` for hard failures.

## UX-03: History tab loses scroll position after autoload

- **Severity:** Low
- **Effort:** Small
- **File:** `src/ui/tabs/history.py:188-195`

`wire_history_autoload` reloads the table every time the History tab is selected. If the user was viewing a detail panel for a specific call, scrolling back up to the table and switching tabs and back will reset the table to the top. Gradio does not preserve scroll across reloads.

**Suggested improvement.** Add a "Pin to row N" option, or limit autoload to first visit by storing a `gr.State` flag.

## UX-04: Accessibility (a11y) is mostly inherited from Gradio defaults

Gradio components render with reasonable ARIA roles out of the box. The custom touches in this app do not break that. A few small reinforcements:

- The "Analyze Call" button (`src/ui/tabs/analyze.py:34-38`) has `variant="primary"` and `size="lg"`, which Gradio renders with sufficient contrast. Good.
- The `gr.Audio` upload (`src/ui/tabs/analyze.py:18-24`) accepts microphone input. Screen-reader announcement of "recording" / "stopped" depends on the browser; this is a Gradio concern, not application code.
- All table headers in `src/ui/tabs/history.py:15` are labeled. Good.

**Suggested improvement.** Wrap the top-of-page `gr.Markdown` (`src/ui/app_builder.py:22-26`) in a `<header>` semantic block. Gradio renders Markdown into `<div>`s by default. The fix is to inject one line of HTML at the top of the page, but it is cosmetic.

## UX-05: PDF and JSON downloads expose temp file paths

- **Severity:** Low (cosmetic privacy leak)
- **File:** `src/services/pipeline.py:155-163`, `src/ui/tabs/history.py:140-152`

The download component shows the on-disk temp path, which includes the OS temp directory (`/tmp/report_xxxxx.json`). On a single-user local install this is fine. On a multi-user HF Space the path is visible to the user who triggered the download but reveals the server's file layout.

**Suggested improvement.** Rename the temp file to a human-friendly name before yielding it: `call-{short_id}-report.json` and `call-{short_id}-report.pdf`. `tempfile.NamedTemporaryFile(prefix=...)` already supports this; the prefix is already partly used at `src/ui/tabs/history.py:141`.

## UX-06: Caller ID and Department fields accept arbitrary strings

- **Severity:** Low
- **File:** `src/ui/tabs/analyze.py:25-33`

Both fields are free-form text boxes. They feed into `caller_id` and `department` and pass through the intake PII scanner. If a user enters a real phone number into `caller_id`, the metadata PII scanner at `src/agents/intake.py:32-47` flags it but does not redact it. The flagged-field info is captured in `IntakeResult.pii_scan` but not shown back to the user.

**Suggested improvement.** Surface the PII scan result on the UI. A small badge ("PII detected in metadata: phone in caller_id") under the Analyze button would be informative without being intrusive.

## UX-07: Observability dashboard is not refreshing automatically

- **Severity:** Low
- **File:** `src/ui/tabs/observability.py:42-49`

The Observability tab autoloads on first selection (`src/ui/app_builder.py:48-51` plus `wire_observability_autoload`), but it does not auto-refresh while the tab is open. A user who leaves it open during a busy run sees stale metrics until they click Refresh.

**Suggested improvement.** Add a `gr.Timer(value=30)` to refresh every 30 seconds while the tab is visible. Gradio 5.x supports timers.

## Strengths Worth Preserving

- The master-detail flow on the History tab (`src/ui/tabs/history.py:90-164`) is correctly wired and handles edge cases (out-of-range indices, missing report JSON) gracefully.
- The pipeline UI explicitly clears stale analysis fields on error (`src/ui/tabs/analyze.py:84-89`). Many comparable Gradio apps display old content from the previous run; this one does not.
- The "Showing up to 200 most recent calls" note (`src/ui/tabs/history.py:45-47`) sets correct user expectations.
- The Observability tab's LangSmith status message at `src/services/observability.py:71-91` provides the exact env vars the user must set, which is the right level of self-documentation.

The UI is more polished than most personal-project Gradio apps. The findings above are refinements, not corrections.
