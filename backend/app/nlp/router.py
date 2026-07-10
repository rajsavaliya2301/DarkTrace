"""NLP analysis API endpoints — analyze, translate, extract entities, classify, sentiment."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.dependencies import (
    get_current_user,
    CurrentUser,
    require_permission,
    log_user_action,
)
from app.nlp.analyzer import get_nlp_analyzer
from app.nlp.entities import get_entity_extractor
from app.nlp.sentiment import get_sentiment_analyzer
from app.nlp.translator import get_translator
from app.nlp.classifier import get_classifier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlp", tags=["NLP & Analysis"])


# ─── Pydantic Schemas ──────────────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Content to analyze through the full NLP pipeline."""
    content_id: str = Field(default="", description="Optional content identifier")
    text: str = Field(..., min_length=1, max_length=100000, description="Text content to analyze")
    title: str = Field(default="", max_length=1000, description="Optional title for context")
    language: str = Field(default="en", max_length=10, description="Language code hint")


class TranslateRequest(BaseModel):
    """Translation request."""
    text: str = Field(..., min_length=1, max_length=50000)
    target_language: str = Field(default="en", max_length=10)
    source_language: Optional[str] = Field(default=None, max_length=10)


class ExtractEntitiesRequest(BaseModel):
    """Entity extraction request."""
    text: str = Field(..., min_length=1, max_length=100000)


class ClassifyRequest(BaseModel):
    """Classification request."""
    text: str = Field(..., min_length=1, max_length=100000)
    title: str = Field(default="", max_length=1000)


class SentimentRequest(BaseModel):
    """Sentiment analysis request."""
    text: str = Field(..., min_length=1, max_length=50000)


class NLPResponse(BaseModel):
    """Standard NLP response wrapper."""
    success: bool
    data: Optional[dict] = None
    message: str = "ok"


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/analyze", response_model=NLPResponse)
async def analyze_content(
    request: Request,
    body: AnalyzeRequest,
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Run full NLP analysis pipeline on the provided text."""
    analyzer = await get_nlp_analyzer()
    result = await analyzer.analyze(
        content_id=body.content_id or "manual-" + str(hash(body.text))[:12],
        text=body.text,
        title=body.title,
        language=body.language,
    )

    await log_user_action(
        request, current_user, "nlp_analyze", "content", body.content_id or "manual",
        details={"language": body.language, "text_length": len(body.text)},
    )

    return NLPResponse(success=True, data=result)


@router.post("/translate", response_model=NLPResponse)
async def translate_text(
    request: Request,
    body: TranslateRequest,
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Translate text between languages."""
    translator = await get_translator()
    if body.source_language:
        translated = await translator.translate(body.text, body.target_language)
        result = {
            "translated_text": translated,
            "source_language": body.source_language,
            "target_language": body.target_language,
        }
    else:
        # Auto-detect source language
        detected = await translator.detect_language(body.text)
        translated = await translator.translate(body.text, body.target_language)
        result = {
            "translated_text": translated,
            "detected_language": detected.get("language"),
            "source_language_name": detected.get("language_name"),
            "target_language": body.target_language,
        }

    return NLPResponse(success=True, data=result)


@router.post("/extract-entities", response_model=NLPResponse)
async def extract_entities(
    request: Request,
    body: ExtractEntitiesRequest,
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Extract entities (IPs, emails, BTC addresses, etc.) from text."""
    extractor = await get_entity_extractor()
    entities = await extractor.extract_all(body.text)

    return NLPResponse(success=True, data=entities)


@router.post("/classify", response_model=NLPResponse)
async def classify_text(
    request: Request,
    body: ClassifyRequest,
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Classify text into threat categories."""
    classifier = await get_classifier()
    classification = await classifier.classify(body.text, body.title)

    return NLPResponse(success=True, data=classification)


@router.post("/sentiment", response_model=NLPResponse)
async def analyze_sentiment(
    request: Request,
    body: SentimentRequest,
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Analyze sentiment of text."""
    analyzer = await get_sentiment_analyzer()
    sentiment = await analyzer.analyze(body.text)

    return NLPResponse(success=True, data=sentiment)
