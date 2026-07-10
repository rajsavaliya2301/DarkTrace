"""ML-based sentiment analysis using HuggingFace transformers."""

import asyncio
import logging
import time
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_sentiment_cache = {}
_cache_ttl = 300

class MLSentimentAnalyzer:
    """Enterprise sentiment analyzer using transformer models."""
    
    def __init__(self):
        self._sentiment_pipeline = None
        self._model_loaded = False
    
    async def ensure_loaded(self):
        if self._model_loaded:
            return True
        try:
            from transformers import pipeline
            from app.config import get_settings
            settings = get_settings()
            
            logger.info("Loading sentiment model: %s", settings.SENTIMENT_MODEL)
            loop = asyncio.get_event_loop()
            self._sentiment_pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "sentiment-analysis",
                    model=settings.SENTIMENT_MODEL,
                    device=-1,
                    cache_dir=settings.MODEL_CACHE_DIR,
                )
            )
            self._model_loaded = True
            logger.info("Sentiment model loaded successfully")
            return True
        except Exception as e:
            logger.warning("Failed to load sentiment model: %s", e)
            self._model_loaded = True
            return False
    
    async def analyze(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using ML model with keyword fallback."""
        if not text or not text.strip():
            return {"threat_intent": 0.0, "hostility": 0.0, "urgency": 0.0,
                    "cooperation": 0.0, "polarity": 0.0, "subjectivity": 0.0}
        
        cache_key = hash(text[:1000]) % 10000000
        if cache_key in _sentiment_cache:
            entry = _sentiment_cache[cache_key]
            if time.time() - entry["time"] < _cache_ttl:
                return entry["result"]
        
        text = text[:2000]  # Truncate
        ml_success = await self.ensure_loaded()
        result = None
        
        if ml_success and self._sentiment_pipeline:
            try:
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(
                    None,
                    lambda: self._sentiment_pipeline(text[:512])
                )
                
                label = output[0]["label"]
                score = output[0]["score"]
                
                # Map binary sentiment to our dimensions
                polarity = score if label.upper() == "POSITIVE" else -score
                threat_intent = max(0.0, -polarity * 0.8)
                hostility = max(0.0, -polarity * 0.6) if polarity < 0 else 0.0
                urgency = min(1.0, abs(polarity) * 0.3)
                
                result = {
                    "threat_intent": round(threat_intent, 4),
                    "hostility": round(hostility, 4),
                    "urgency": round(urgency, 4),
                    "cooperation": round(max(0.0, polarity * 0.4), 4) if polarity > 0 else 0.0,
                    "polarity": round(polarity, 4),
                    "subjectivity": round(abs(polarity), 4),
                    "classifier": "ml_transformer",
                }
            except Exception as e:
                logger.warning("ML sentiment failed: %s", e)
        
        # Fallback to existing keyword-based sentiment
        if result is None:
            from app.nlp.sentiment import get_sentiment_analyzer
            fallback = await get_sentiment_analyzer()
            result = await fallback.analyze(text)
            result["classifier"] = "keyword_fallback"
        
        _sentiment_cache[cache_key] = {"result": result, "time": time.time()}
        return result


_ml_sentiment: Optional[MLSentimentAnalyzer] = None

async def get_ml_sentiment() -> MLSentimentAnalyzer:
    global _ml_sentiment
    if _ml_sentiment is None:
        _ml_sentiment = MLSentimentAnalyzer()
    return _ml_sentiment
