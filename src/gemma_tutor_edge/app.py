from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .llm import build_model
from .schemas import (
    ChatRequest,
    HealthResponse,
    QueueJobRequest,
    ReadyPackLaunchRequest,
    ToeicAnswerRequest,
    ToeicNextRequest,
    WorkerStartRequest,
    QuizGenerateRequest,
    QuizSubmitRequest,
)
from .services import (
    analyze_image,
    generate_quiz,
    get_toeic_next_item,
    handle_chat,
    launch_ready_pack,
    queue_background_job,
    submit_toeic_answer,
    submit_quiz,
)
from .storage import SqliteStore
from .worker_control import WorkerController


settings = get_settings()
store = SqliteStore(settings.app_db_path)
model = build_model(settings)
worker_controller = WorkerController(project_root=Path(__file__).resolve().parents[2])


@asynccontextmanager
async def lifespan(app: FastAPI):
    await store.init()
    try:
        yield
    finally:
        worker_controller.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    model_name = settings.google_model if settings.llm_backend == "google" else settings.llama_model
    return HealthResponse(status="ok", backend=settings.llm_backend, model_name=model_name)


@app.post("/v1/chat")
async def chat(request: ChatRequest):
    try:
        return await handle_chat(model=model, store=store, request=request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/quiz/generate")
async def quiz_generate(request: QuizGenerateRequest):
    try:
        return await generate_quiz(model=model, store=store, request=request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/quiz/submit")
async def quiz_submit(request: QuizSubmitRequest):
    try:
        return await submit_quiz(store=store, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/quiz/next")
async def quiz_next(request: ToeicNextRequest):
    try:
        return await get_toeic_next_item(store=store, request=request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/quiz/answer")
async def quiz_answer(request: ToeicAnswerRequest):
    try:
        return await submit_toeic_answer(store=store, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/v1/dashboard/{user_id}")
async def dashboard(user_id: str):
    try:
        return await store.dashboard_overview(user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/v1/dashboard/{user_id}/detail")
async def dashboard_detail(user_id: str):
    try:
        return await store.dashboard_detail(user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/v1/packs/ready/{user_id}")
async def ready_packs(user_id: str):
    try:
        return await store.list_ready_packs(user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/packs/ready/{ready_pack_id}/launch")
async def ready_pack_launch(ready_pack_id: str, request: ReadyPackLaunchRequest):
    try:
        return await launch_ready_pack(store=store, ready_pack_id=ready_pack_id, request=request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/v1/jobs/{user_id}")
async def list_jobs(user_id: str):
    try:
        return await store.list_active_jobs(user_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/jobs/queue")
async def queue_job(request: QueueJobRequest):
    try:
        return await queue_background_job(store=store, request=request)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/v1/worker/status")
async def worker_status():
    return worker_controller.status()


@app.post("/v1/worker/start")
async def worker_start(request: WorkerStartRequest):
    try:
        return worker_controller.start(
            poll_interval=request.poll_interval,
            max_jobs=request.max_jobs,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/worker/stop")
async def worker_stop():
    try:
        return worker_controller.stop()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/v1/image/analyze")
async def image_analyze(
    user_id: str = Form(...),
    prompt: str = Form("Analyze this image and turn it into English learning material."),
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        return await analyze_image(
            model=model,
            store=store,
            user_id=user_id,
            prompt=prompt,
            image_bytes=content,
            media_type=file.content_type or "image/png",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc
