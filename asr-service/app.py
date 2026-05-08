import asyncio
import logging
import os
import threading
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from faster_whisper import WhisperModel

import requests

APP_NAME = "asr-service"
logger = logging.getLogger("uvicorn.error")

# ======= Fixed ASR settings (не приходят из запроса) =======
MODEL_SIZE = "medium"  # фиксируем medium
MODEL_ID = os.getenv("ASR_MODEL_ID", MODEL_SIZE)
MODEL_PATH = os.getenv("ASR_MODEL_PATH", f"/models/faster-whisper-{MODEL_SIZE}")
LOCAL_FILES_ONLY = os.getenv("ASR_LOCAL_FILES_ONLY", "true").strip().lower() in {"1", "true", "yes", "on"}
DEVICE = os.getenv("ASR_DEVICE", "cuda")  # "cuda" или "cpu"
COMPUTE_TYPE = os.getenv("ASR_COMPUTE_TYPE", "float16")  # GPU: float16/int8_float16; CPU: int8/float32
CPU_THREADS = int(os.getenv("ASR_CPU_THREADS", "4"))
NUM_WORKERS = int(os.getenv("ASR_NUM_WORKERS", "1"))
MAX_CONCURRENT_TRANSCRIBES = int(os.getenv("ASR_MAX_CONCURRENT_TRANSCRIBES", "1"))

# Fixed decoding params:
LANGUAGE = "ru"
VAD_FILTER = True
WORD_TIMESTAMPS = True
BEAM_SIZE = 1

app = FastAPI(title=APP_NAME, version="1.0.0")

# Модель грузим 1 раз при старте процесса
model: Optional[WhisperModel] = None
transcribe_executor: Optional[ThreadPoolExecutor] = None
transcribe_semaphore: Optional[asyncio.Semaphore] = None
active_transcribes = 0
active_transcribes_lock = threading.Lock()


class Word(BaseModel):
    start: float
    end: float
    word: str


class Segment(BaseModel):
    start: float
    end: float
    text: str
    words: List[Word] = []


class TranscribeResponse(BaseModel):
    duration: float
    language: str
    language_probability: float
    segments: List[Segment]


@app.on_event("startup")
async def startup() -> None:
    global model, transcribe_executor, transcribe_semaphore
    # cpu_threads только для CPU, для cuda можно оставить 0
    cpu_threads = CPU_THREADS if DEVICE == "cpu" else 0
    max_concurrent = max(1, MAX_CONCURRENT_TRANSCRIBES)

    try:
        resolved_model_path = MODEL_PATH
        model_bin_path = os.path.join(MODEL_PATH, "model.bin")
        if not os.path.exists(model_bin_path):
            if LOCAL_FILES_ONLY:
                raise RuntimeError(
                    f"Local ASR model was not found at {MODEL_PATH}. "
                    "Build the image with the model preloaded or disable ASR_LOCAL_FILES_ONLY."
                )
            print(f"[asr-service] Downloading model {MODEL_ID} into {MODEL_PATH}", flush=True)
            resolved_model_path = download_model(MODEL_ID, output_dir=MODEL_PATH, local_files_only=False)
        print(
            f"[asr-service] Initializing WhisperModel from {resolved_model_path} "
            f"(device={DEVICE}, compute_type={COMPUTE_TYPE})",
            flush=True,
        )
        model = WhisperModel(
            resolved_model_path,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            cpu_threads=cpu_threads,
            num_workers=NUM_WORKERS,
            local_files_only=LOCAL_FILES_ONLY,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to init WhisperModel: {e}") from e


@app.on_event("shutdown")
def shutdown() -> None:
    if transcribe_executor is not None:
        transcribe_executor.shutdown(wait=False, cancel_futures=True)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "model": MODEL_SIZE,
        "model_id": MODEL_ID,
        "model_path": MODEL_PATH,
        "model_ready": model is not None,
        "local_files_only": LOCAL_FILES_ONLY,
        "device": DEVICE,
        "compute_type": COMPUTE_TYPE,
        "num_workers": NUM_WORKERS,
        "cpu_threads": CPU_THREADS,
        "max_concurrent_transcribes": MAX_CONCURRENT_TRANSCRIBES,
        "fixed_params": {
            "language": LANGUAGE,
            "vad_filter": VAD_FILTER,
            "word_timestamps": WORD_TIMESTAMPS,
            "beam_size": BEAM_SIZE,
        },
    }


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...), ) -> TranscribeResponse:
    """
    Принимаем аудио. Никаких query-параметров для модели не принимаем.
    """
    global model, transcribe_executor, transcribe_semaphore
    if model is None or transcribe_executor is None or transcribe_semaphore is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    request_id = uuid.uuid4().hex[:8]
    original_filename = file.filename or "audio"
    queued_at = time.perf_counter()
    logger.info(
        "ASR request queued request_id=%s filename=%s max_concurrent=%s",
        request_id,
        original_filename,
        MAX_CONCURRENT_TRANSCRIBES,
    )

    # Сохраняем во временный файл, потому что faster-whisper ожидает путь/файл
    suffix = os.path.splitext(file.filename or "")[1] or ".audio"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read upload: {e}")

    try:
        async with transcribe_semaphore:
            wait_sec = time.perf_counter() - queued_at
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                transcribe_executor,
                transcribe_file,
                tmp_path,
                request_id,
                original_filename,
                wait_sec,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR error: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def transcribe_file(
    tmp_path: str,
    request_id: str,
    original_filename: str,
    wait_sec: float,
) -> TranscribeResponse:
    if model is None:
        raise RuntimeError("Model not initialized")

    global active_transcribes
    started_at = time.perf_counter()
    with active_transcribes_lock:
        active_transcribes += 1
        active_now = active_transcribes
    logger.info(
        "ASR transcribe started request_id=%s filename=%s active=%s thread=%s waited_sec=%.3f",
        request_id,
        original_filename,
        active_now,
        threading.current_thread().name,
        wait_sec,
    )

    try:
        segments_iter, info = model.transcribe(
            tmp_path,
            language=LANGUAGE,
            vad_filter=VAD_FILTER,
            word_timestamps=WORD_TIMESTAMPS,
            beam_size=BEAM_SIZE,
        )

        segments_out: List[Segment] = []
        for s in segments_iter:
            words_out: List[Word] = []
            if s.words:
                for w in s.words:
                    words_out.append(Word(start=float(w.start), end=float(w.end), word=str(w.word)))
            segments_out.append(
                Segment(
                    start=float(s.start),
                    end=float(s.end),
                    text=str(s.text),
                    words=words_out,
                )
            )

        elapsed_sec = time.perf_counter() - started_at
        logger.info(
            "ASR transcribe completed request_id=%s filename=%s active=%s elapsed_sec=%.3f audio_duration_sec=%.3f segments=%s",
            request_id,
            original_filename,
            active_now,
            elapsed_sec,
            float(info.duration or 0.0),
            len(segments_out),
        )

        return TranscribeResponse(
            duration=float(info.duration or 0.0),
            language=str(info.language or LANGUAGE),
            language_probability=float(info.language_probability or 0.0),
            segments=segments_out,
        )
    finally:
        with active_transcribes_lock:
            active_transcribes -= 1
