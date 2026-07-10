"""Watchlist keyword matching engine — matches content against watchlist keywords and patterns."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_mongodb

logger = logging.getLogger(__name__)


class KeywordMatcher:
    """Matches content against user-defined watchlist keywords and regex patterns."""

    def __init__(self):
        self._compiled_patterns: Dict[str, List[Tuple[str, re.Pattern, str]]] = {}
        self._cache_time = 0
        self._cache_ttl = 60  # seconds

    async def match_all(self, text: str) -> Dict:
        """Match text against all active watchlists."""
        if not text:
            return {"matched_keywords": [], "matched_patterns": [], "matched_watchlists": [], "severity_boost": 0}

        db = await get_mongodb()
        watchlists = await self._get_active_watchlists(db)

        matched_keywords = []
        matched_patterns = []
        matched_watchlists = []
        total_severity_boost = 0

        text_lower = text.lower()

        for wl in watchlists:
            wl_id = str(wl["_id"])
            wl_name = wl.get("name", "Unknown")

            # Keyword matching
            for keyword in wl.get("keywords", []):
                if not keyword:
                    continue
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    if keyword not in matched_keywords:
                        matched_keywords.append(keyword)
                    if wl_id not in [m["id"] for m in matched_watchlists]:
                        matched_watchlists.append({
                            "id": wl_id,
                            "name": wl_name,
                            "severity_boost": wl.get("severity_boost", 0),
                        })

            # Regex pattern matching
            for regex_entry in wl.get("regex_patterns", []):
                pattern_str = regex_entry.get("pattern", "")
                label = regex_entry.get("label", "")
                case_sensitive = regex_entry.get("case_sensitive", False)

                if not pattern_str:
                    continue

                try:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    compiled = re.compile(pattern_str, flags)
                    matches = compiled.findall(text)
                    if matches:
                        matched_patterns.append({
                            "pattern": pattern_str,
                            "label": label,
                            "matches": matches[:5],  # Limit stored matches
                            "count": len(matches),
                        })
                        if wl_id not in [m["id"] for m in matched_watchlists]:
                            matched_watchlists.append({
                                "id": wl_id,
                                "name": wl_name,
                                "severity_boost": wl.get("severity_boost", 0),
                            })
                except re.error as e:
                    logger.warning("Invalid regex pattern '%s': %s", pattern_str, e)

        # Calculate total severity boost
        total_severity_boost = sum(m.get("severity_boost", 0) for m in matched_watchlists)

        return {
            "matched_keywords": list(set(matched_keywords)),
            "matched_patterns": matched_patterns,
            "matched_watchlists": matched_watchlists,
            "severity_boost": total_severity_boost,
        }

    async def _get_active_watchlists(self, db: AsyncIOMotorDatabase) -> list:
        """Get all active watchlists with caching."""
        import time
        now = time.time()

        if now - self._cache_time > self._cache_ttl:
            cursor = db.watchlists.find({"is_active": True})
            self._cached_watchlists = await cursor.to_list(length=None)
            self._cache_time = now

        return self._cached_watchlists


# Singleton
_keyword_matcher: Optional[KeywordMatcher] = None


async def get_keyword_matcher() -> KeywordMatcher:
    """Get or create the singleton keyword matcher."""
    global _keyword_matcher
    if _keyword_matcher is None:
        _keyword_matcher = KeywordMatcher()
    return _keyword_matcher
