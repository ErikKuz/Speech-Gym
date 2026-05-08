FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ASR_MODEL_PATH=/models/faster-whisper-medium \
    ASR_LOCAL_FILES_ONLY=true

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates; \
    echo 'Acquire::Retries "10"; Acquire::http::Timeout "60"; Acquire::https::Timeout "60"; Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99net; \
    (sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list 2>/dev/null || true); \
    (sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true); \
    apt-get update; \
    apt-get install -y --no-install-recommends ffmpeg; \
    rm -rf /var/lib/apt/lists/*



WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /models && \
    python -c "from faster_whisper import download_model; download_model('medium', output_dir='/models/faster-whisper-medium', local_files_only=False)"

COPY app.py .

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host=0.0.0.0", "--port=8000"]
