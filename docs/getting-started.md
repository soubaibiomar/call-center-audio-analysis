# Getting Started

The shortest path from a fresh checkout to an analyzed call. If anything below disagrees with the top-level `README.md`, the README is the source of truth for production use; this document is the simplified developer onramp.

## Prerequisites

- Python 3.11 or later (3.11 and 3.12 are both tested).
- `ffmpeg` available on `PATH` (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Debian / Ubuntu, `choco install ffmpeg` on Windows).
- At least one LLM API key. The cheapest path is a free Groq key.

## Clone and Install

```bash
git clone https://github.com/ANI-IN/Call-Center-Intelligence-System.git
cd Call-Center-Intelligence-System

python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate

pip install -e ".[dev]"
pre-commit install
```

The first install pulls in roughly 1 GB of dependencies (`torch`, `ctranslate2`, `faster-whisper`, the LangChain stack). It usually takes 2 to 4 minutes on a fresh machine.

## Configure

```bash
cp .env.example .env
```

Then edit `.env`. The simplest free configuration is:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
WHISPER_MODEL_SIZE=tiny
```

If you have an OpenAI key:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your_key_here
WHISPER_MODEL_SIZE=tiny
```

For the full list of variables see `README.md#configuration` or `.env.example`.

## Run the App

```bash
make run
```

The first run downloads the Whisper `tiny` model (about 40 MB). The Gradio UI then opens at `http://127.0.0.1:7860`. If you forgot to set an LLM key, the app prints `Required environment variable OPENAI_API_KEY is not set` at startup.

## Analyze Your First Call

1. Open the **Analyze Call** tab.
2. Upload one of the bundled sample MP3s from `data/samples/` (for example `sample_01.mp3`).
3. Leave Caller ID and Department blank for now.
4. Click **Analyze Call**.
5. Wait 1 to 4 minutes for the pipeline (faster with GPU). The transcript, summary, and QA scores appear below; PDF and JSON downloads are at the bottom.

To browse past analyses, switch to the **All MP3 History** tab.

To see pipeline metrics and the audit trail, switch to the **Observability** tab.

## Run the Tests

```bash
make test                    # 109 unit + security tests, under 20 seconds
make test-integration        # full pipeline (needs an LLM key)
make test-all                # everything
```

The unit suite is the fast feedback loop. It does not touch any external API and finishes in under 20 seconds on a typical laptop.

## Format and Lint

```bash
make lint                    # ruff check + format --check (read-only)
make format                  # ruff check --fix + ruff format (writes)
make typecheck               # mypy strict on src/
make secret-scan             # detect-secrets baseline scan
```

These commands match the pre-commit hooks at `.pre-commit-config.yaml:1-21`. Running them locally before pushing avoids the surprise of a hook failure later.

## Common Issues

| Problem | Fix |
|---|---|
| `ffmpeg: command not found` | Install ffmpeg (see Prerequisites). |
| `Required environment variable OPENAI_API_KEY is not set` | Set the key in `.env` or switch `LLM_PROVIDER` to `gemini` / `groq`. |
| Whisper download is slow | The first transcription downloads the model from Hugging Face. Subsequent runs use the local cache. |
| Pipeline takes 5+ minutes per call | You are on CPU with `WHISPER_MODEL_SIZE` other than `tiny`. Either set it to `tiny` or attach a GPU. |
| Port 7860 is busy | Set `GRADIO_SERVER_PORT=7861 python app.py` to choose a different port. |
| `make` is missing on Windows | Use the explicit commands directly: `pytest tests/unit/ tests/security/ -v`, `ruff check ...`, etc. |

## Next Steps

- Read `docs/architecture.md` for the deep view of how the pipeline is wired.
- Read `CONTRIBUTING.md` for branch and PR conventions.
- Read `SECURITY.md` if you plan to deploy the system to the public internet.
