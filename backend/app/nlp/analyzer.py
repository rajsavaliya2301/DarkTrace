"""Main NLP pipeline — orchestrates entity extraction, sentiment, translation, classification, keyword matching."""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional

from app.nlp.entities import get_entity_extractor
from app.nlp.translator import get_translator
from app.nlp.keyword_matcher import get_keyword_matcher
from app.config import get_settings
from app.database import get_mongodb, get_elasticsearch

logger = logging.getLogger(__name__)


class NLPAnalyzer:
    """Main NLP pipeline that orchestrates all analysis components."""

    async def analyze(self, content_id: str, text: str, title: str = "", language: str = "en") -> Dict:
        """Run full NLP analysis pipeline on content."""
        start_time = time.time()
        logger.info("Starting NLP analysis for content %s", content_id)

        # Stage 1: Language detection
        translator = await get_translator()
        detected_lang = await translator.detect_language(text)
        actual_lang = detected_lang.get("language", language)

        # Stage 2: Translation (if not English)
        translated_text = None
        if actual_lang != "en":
            translated_text = await translator.translate(text, "en")
            analysis_text = translated_text or text
        else:
            analysis_text = text

        # Stage 2.5: Dark web text preprocessing
        try:
            dw_features = await translator.detect_darkweb_variants(analysis_text)
            analysis_text = await translator.preprocess_darkweb_text(analysis_text)
            logger.debug("Dark web preprocessing: %s", dw_features.get("variant", "standard"))
        except Exception as e:
            logger.debug("Dark web preprocessing skipped: %s", e)

        # Stage 3: Entity extraction
        extractor = await get_entity_extractor()
        entities = await extractor.extract_all(analysis_text)

        # Stage 4: Keyword matching
        matcher = await get_keyword_matcher()
        keyword_results = await matcher.match_all(analysis_text)

        # Merge keyword matches into entities
        entities["keywords_matched"] = keyword_results.get("matched_keywords", [])

        # Stage 5: ML-based sentiment analysis
        from app.nlp.ml_sentiment import get_ml_sentiment
        ml_sentiment = await get_ml_sentiment()
        sentiment = await ml_sentiment.analyze(analysis_text)

        # Stage 6: ML-based Threat classification (zero-shot)
        from app.nlp.ml_classifier import get_ml_classifier
        ml_classifier = await get_ml_classifier()
        classification = await ml_classifier.classify(analysis_text, title)

        # Compile results
        analysis_result = {
            "content_id": content_id,
            "language_detection": detected_lang,
            "translated_text": translated_text,
            "entities": entities,
            "keyword_matches": keyword_results,
            "sentiment": sentiment,
            "classification": classification,
            "processing_time_ms": round((time.time() - start_time) * 1000, 1),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "NLP analysis for %s completed in %.1fms. Classification: %s (%.1f%%)",
            content_id,
            analysis_result["processing_time_ms"],
            classification["primary"],
            classification["confidence"] * 100,
        )

        return analysis_result

    async def analyze_and_store(self, content_id: str, text: str, title: str = "", language: str = "en") -> Dict:
        """Run NLP analysis and store results in MongoDB and Elasticsearch."""
        analysis = await self.analyze(content_id, text, title, language)

        try:
            db = await get_mongodb()
            # Update raw_content with analysis results
            await db.raw_content.update_one(
                {"_id": content_id},
                {
                    "$set": {
                        "processing_status": "analyzed",
                        "analyzed_at": datetime.now(timezone.utc),
                        "analysis": analysis,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )

            # Update Elasticsearch index
            try:
                es = await get_elasticsearch()
                await es.update(
                    index="crawled_content",
                    id=content_id,
                    body={
                        "doc": {
                            "analysis": {
                                "sentiment": analysis["sentiment"],
                                "classification": analysis["classification"],
                            },
                            "entities": analysis["entities"],
                            "language": analysis["language_detection"]["language"],
                            "translated_text": analysis.get("translated_text"),
                            "processing_status": "analyzed",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        }
                    },
                )
            except Exception as e:
                logger.warning("ES update failed for analysis %s: %s", content_id, e)

        except Exception as e:
            logger.error("Failed to store analysis for %s: %s", content_id, e)

        return analysis


# Singleton
_nlp_analyzer: Optional[NLPAnalyzer] = None


async def get_nlp_analyzer() -> NLPAnalyzer:
    """Get or create the singleton NLP analyzer."""
    global _nlp_analyzer
    if _nlp_analyzer is None:
        _nlp_analyzer = NLPAnalyzer()
    return _nlp_analyzer
