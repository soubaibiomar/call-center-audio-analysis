# Local typing boundaries

Mypy loads these interfaces through `mypy_path` in `pyproject.toml`. They describe
only the APIs this application consumes from faster-whisper 1.2.1 and soundfile
0.13.1, which do not publish usable typing markers for this environment. They do
not replace either runtime package or claim full library coverage.

Whisper segment fields are concrete. Provider-specific transcription options and
soundfile's accepted array representations remain explicitly dynamic (`Any`).
The cached-model Docker smoke and existing audio tests exercise the real packages.
Review these interfaces when changing those pinned versions or adding API usage.

ReportLab uses the version-pinned `types-reportlab` development package instead.
Strict mypy checks all application modules, both service packages and `app.py`;
missing imports and untyped definitions remain errors. Optional PyTorch detection
uses `importlib.import_module`, retaining the original CPU fallback when absent.
