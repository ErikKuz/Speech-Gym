import os
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from faster_whisper import WhisperModel, download_model

APP_NAME = "asr-service"

# ======= Fixed ASR settings (не приходят из запроса) =======
MODEL_SIZE = "medium"  # фиксируем medium
MODEL_ID = os.getenv("ASR_MODEL_ID", MODEL_SIZE)
MODEL_PATH = os.getenv("ASR_MODEL_PATH", f"/models/faster-whisper-{MODEL_SIZE}")
LOCAL_FILES_ONLY = os.getenv("ASR_LOCAL_FILES_ONLY", "true").strip().lower() in {"1", "true", "yes", "on"}
DEVICE = os.getenv("ASR_DEVICE", "cuda")  # "cuda" или "cpu"
COMPUTE_TYPE = os.getenv("ASR_COMPUTE_TYPE", "float16")  # GPU: float16/int8_float16; CPU: int8/float32
CPU_THREADS = int(os.getenv("ASR_CPU_THREADS", "4"))
NUM_WORKERS = int(os.getenv("ASR_NUM_WORKERS", "1"))

# Fixed decoding params:
LANGUAGE = "ru"
VAD_FILTER = True
WORD_TIMESTAMPS = True
BEAM_SIZE = 5

app = FastAPI(title=APP_NAME, version="1.0.0")

# Модель грузим 1 раз при старте процесса
model: Optional[WhisperModel] = None


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
def startup() -> None:
    global model
    # cpu_threads только для CPU, для cuda можно оставить 0
    cpu_threads = CPU_THREADS if DEVICE == "cpu" else 0

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
        print("[asr-service] WhisperModel initialized successfully", flush=True)
    except Exception as e:
        raise RuntimeError(f"Failed to init WhisperModel: {e}") from e


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
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

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

        return TranscribeResponse(
            duration=float(info.duration or 0.0),
            language=str(info.language or LANGUAGE),
            language_probability=float(info.language_probability or 0.0),
            segments=segments_out,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ASR error: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
