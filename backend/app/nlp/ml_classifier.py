"""ML-based threat classifier using HuggingFace zero-shot classification for production dark web intelligence."""

import asyncio
import logging
import time
from typing import Dict, List, Optional
from functools import lru_cache
from app.config import get_settings

logger = logging.getLogger(__name__)

# Cache for classification results
_classification_cache = {}
_cache_ttl = 300  # 5 minutes

class MLThreatClassifier:
    """Enterprise-grade threat classifier using HuggingFace zero-shot classification."""
    
    # Threat categories for zero-shot classification (must match existing categories)
    CANDIDATE_LABELS = [
        "ransomware", "malware", "exploit", "data_breach", "fraud",
        "illegal_goods", "services", "intelligence", "hacktivism",
        "carding", "identity_theft", "drugs", "weapons", "terrorism",
        "extremism", "weapons_trafficking", "human_trafficking",
        "narcotics", "cyber_espionage", "financial_fraud",
    ]
    
    def __init__(self):
        self._classifier = None
        self._model_loaded = False
        self._fallback_classifier = None  # Will use existing ThreatClassifier as fallback
    
    async def ensure_loaded(self):
        """Lazy-load the HuggingFace zero-shot classifier."""
        if self._model_loaded:
            return True
            
        settings = get_settings()
        try:
            from transformers import pipeline
            logger.info("Loading zero-shot classification model: %s", settings.HUGGINGFACE_MODEL)
            
            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._classifier = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "zero-shot-classification",
                    model=settings.HUGGINGFACE_MODEL,
                    device=-1,  # CPU
                    cache_dir=settings.MODEL_CACHE_DIR,
                )
            )
            self._model_loaded = True
            logger.info("Zero-shot classifier loaded successfully")
            return True
        except Exception as e:
            logger.warning("Failed to load zero-shot model: %s. Using fallback classifier.", e)
            self._model_loaded = True  # Don't retry on every call
            return False
    
    async def classify(self, text: str, title: str = "") -> Dict:
        """Classify text using ML zero-shot classification with keyword fallback."""
        combined = f"{title} {text}" if title else text
        if not combined.strip():
            return {"primary": "unknown", "secondary": [], "confidence": 0.0, "all_scores": {}}
        
        # Truncate for performance (max 1000 tokens)
        combined = combined[:5000]
        
        # Check cache
        cache_key = hash(combined) % 10000000
        if cache_key in _classification_cache:
            entry = _classification_cache[cache_key]
            if time.time() - entry["time"] < _cache_ttl:
                return entry["result"]
        
        # Try ML classification
        ml_success = await self.ensure_loaded()
        result = None
        
        if ml_success and self._classifier:
            try:
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(
                    None,
                    lambda: self._classifier(combined[:500], self.CANDIDATE_LABELS, multi_label=False)
                )
                
                scores = {}
                for label, score in zip(output["labels"], output["scores"]):
                    scores[label] = round(float(score), 4)
                
                sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                primary = sorted_scores[0][0] if sorted_scores[0][1] > 0.05 else "unknown"
                confidence = sorted_scores[0][1] if sorted_scores else 0.0
                secondary = [cat for cat, sc in sorted_scores[1:4] if sc > 0.1]
                
                result = {
                    "primary": primary,
                    "secondary": secondary,
                    "confidence": round(float(confidence), 4),
                    "all_scores": scores,
                    "classifier": "ml_zero_shot",
                }
            except Exception as e:
                logger.warning("ML classification failed: %s", e)
        
        # Fallback: use existing keyword-based ThreatClassifier
        if result is None:
            from app.nlp.classifier import get_classifier
            fallback = await get_classifier()
            result = await fallback.classify(text, title)
            result["classifier"] = "keyword_fallback"
        
        # Cache result
        _classification_cache[cache_key] = {"result": result, "time": time.time()}
        
        return result
    
    async def get_categories(self) -> List[str]:
        """Return list of all supported categories."""
        return self.CANDIDATE_LABELS.copy()


# Singleton pattern
_ml_classifier: Optional[MLThreatClassifier] = None

async def get_ml_classifier() -> MLThreatClassifier:
    global _ml_classifier
    if _ml_classifier is None:
        _ml_classifier = MLThreatClassifier()
    return _ml_classifier
