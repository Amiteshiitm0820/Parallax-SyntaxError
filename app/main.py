"""FastAPI entry point: routes and CORS only. Logic lives in app/services/."""
import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalyzeRequest, AnalyzeResponse, FeedbackRequest, FeedbackResponse
from app.services.analyzer import analyze_message
from app.services.feedback import save_feedback
from app.services.llm import LLMError, get_llm_client

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="TrustLens Analysis API", version="0.1.0")

# Frontend dev server ports. Add your teammate's port here if different.
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:8501",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _llm():
    return get_llm_client()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.message_text.strip():
        raise HTTPException(status_code=400, detail="message_text cannot be empty.")
    try:
        _, response = analyze_message(req, _llm())
        # analysis_id is already set on the response object by analyze_message()
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return response


@app.post("/api/report-false-positive", response_model=FeedbackResponse)
def report_false_positive(req: FeedbackRequest):
    save_feedback(req.model_dump())
    return FeedbackResponse(status="success", message="Feedback recorded.")
