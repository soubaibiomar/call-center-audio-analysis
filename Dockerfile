# Production-ish container image for the Call Center Intelligence System.
# Mirrors the HuggingFace Space configuration so the same image can be run
# locally, on Fly.io, Render, or any container host.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

# ffmpeg is needed by faster-whisper / soundfile for non-WAV inputs.
# build-essential is occasionally required by ctranslate2 wheels on slim images.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first so the layer caches across source-only changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source.
COPY app.py ./
COPY src/ ./src/
COPY data/samples/ ./data/samples/

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser \
 && mkdir -p /app/data \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# Single-process Gradio app. The entrypoint will auto-detect the SPACE_ID env
# var when run on HuggingFace Spaces; outside of that it binds to 0.0.0.0:7860
# because GRADIO_SERVER_NAME is set above.
CMD ["python", "app.py"]
