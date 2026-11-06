FROM project28-step13-qwen:headers
# Separate runtime: Qwen's pinned Transformers remains in its original image.
RUN python -m pip uninstall -y qwen-asr gradio gradio-client sentence-transformers && \
    python -m pip install --no-cache-dir 'transformers==5.21.1' \
    'accelerate==1.15.0' 'faster-whisper==1.2.1'
ENV HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
WORKDIR /workspace
