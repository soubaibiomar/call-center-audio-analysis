FROM project28-upgrade-benchmark:local
# CTranslate2 needs CUDA 12 libraries; keep them out of Torch's CUDA 13 paths.
RUN python -m pip install --no-cache-dir --target /opt/ct2-cuda \
    'nvidia-cublas-cu12==12.9.1.4' 'nvidia-cudnn-cu12==9.10.2.21'
ENV LD_LIBRARY_PATH=/opt/ct2-cuda/nvidia/cublas/lib:/opt/ct2-cuda/nvidia/cudnn/lib
