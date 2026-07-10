"""Search API endpoint — full-text search with faceted filters across all indices."""

import json
import logging
import re
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from elasticsearch import AsyncElasticsearch

from app.dependencies import get_es, get_current_user, CurrentUser, require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])

# ─── Indian PII Pattern Compilation ──────────────────────────────────────────

INDIAN_PII_PATTERNS = {
    "aadhaar": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    "mobile": re.compile(r"(?:\+91[-\s]?|0)[6-9]\d{9}"),
    "voter_id": re.compile(r"\b[A-Z]{3}[0-9]{7}\b"),
    "passport": re.compile(r"\b[A-Z][0-9]{7}\b"),
    "driving_license": re.compile(r"\b(?:[A-Z]{2}\d{2}|[A-Z]{2}\d{13})\b"),
    "upi": re.compile(r"\b[\w.-]+@[a-zA-Z]{3,}\b"),
    "gst": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}\b"),
    "ifsc": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),
}

# Indian context synonym expansion map — when a user searches these terms,
# we boost documents containing related Indian-context keywords
INDIAN_SYNONYM_MAP = {
    "aadhaar": ["aadhaar", "uidai", "aadhar", "aadhaar number", "UID", "unique id", "biometric id", "आधार"],
    "pan": ["pan", "pan card", "income tax", "taxpayer", "permanent account number", "पैन"],
    "passport": ["passport", "passport seva", " passport ", "travel document", "visa", "पासपोर्ट"],
    "voter": ["voter id", "voter card", "epic card", "election card", "voter list", "मतदाता"],
    "bank": ["bank account", "hdfc", "icici", "sbi", "axis", "kotak", "yes bank", "banking", "nrega", "bank statement", "बैंक"],
    "aadhaar pan": ["aadhaar pan link", "income tax return", "itr filing", "tax fraud", "pan aadhaar"],
    "upi": ["upi", "gpay", "google pay", "phonepe", "paytm", "bhim", "unified payments interface", "भीम", "यूपीआई"],
    "cvv dumps": ["cvv", "dumps", "fullz", "credit card", "debit card", "carding", "bin", "track 1", "track 2"],
    "ransomware": ["ransomware", "lockbit", "blackcat", "alphv", "conti", "ransom", "decryptor", "ransom note", "encrypt"],
    "terror": ["terrorism", "terrorist", "isis", "jihad", "mujahid", "mujahideen", "terror", "bomb", "ied", "explosive", "आतंकवाद", "जिहाद"],
    "drugs": ["drugs", "cocaine", "heroin", "fentanyl", "meth", "narcotics", "mdma", "ecstasy", "opium", "ड्रग्स"],
    "weapons": ["weapons", "arms", "ak-47", "pistol", "rifle", "ammunition", "gun", "firearm", "हथियार"],
    "human trafficking": ["trafficking", "human trafficking", "forced labor", "sex trafficking", "modern slavery", "मानव तस्करी"],
    "data leak": ["data leak", "data breach", "database dump", "leaked", "breach", "exposed", "credential dump", "डेटा लीक"],
    "china cyber": ["china cyber", "chinese hacker", "apt china", "pla cyber", "mss", "网络攻击", "中国黑客", "网络间谍"],
    "pakistan cyber": ["pakistan cyber", "isi cyber", "pakistani hacker", "巴基斯坦", "پاکستان"],
    "iran cyber": ["iran cyber", "iranian hacker", "apt iran", "سايبر", "جاسوسي"],
    "russia cyber": ["russia cyber", "russian hacker", "apt russia", "fsb", "gru", "кибератака"],
}

# Hindi<>English transliteration mappings for common threat/search terms
HINDI_TRANSLITERATION = {
    "aadhaar": "आधार",
    "aadhar": "आधार",
    "pan": "पैन",
    "passport": "पासपोर्ट",
    "voter": "मतदाता",
    "bank": "बैंक",
    "terror": "आतंक",
    "jihad": "जिहाद",
    "drugs": "ड्रग्स",
    "weapons": "हथियार",
    "credit card": "क्रेडिट कार्ड",
    "data leak": "डेटा लीक",
    "hack": "हैक",
    "malware": "मैलवेयर",
    "ransomware": "रैनसमवेयर",
    "phishing": "फ़िशिंग",
    "fraud": "धोखाधड़ी",
    "scam": "स्कैम",
    "identity theft": "पहचान की चोरी",
    # Urdu/Perso-Arabic transliterations for threat search
    "jihad": "جهاد",
    "terrorism": "دہشت گردی",
    "attack": "حملہ",
    "bomb": "بم",
    "weapon": "اسلحہ",
    "drugs": "منشیات",
    "trafficking": "سمگلنگ",
    # Chinese transliterations
    "cyber attack": "网络攻击",
    "hacker": "黑客",
    "data leak": "数据泄露",
    "espionage": "间谍",
    "malware": "恶意软件",
    # Russian transliterations
    "attack": "атака",
    "hack": "взлом",
    "leak": "утечка",
}


def _expand_query_with_synonyms(q: str) -> str:
    """Expand a search query with Indian-context synonyms for better recall."""
    q_lower = q.lower().strip()
    expanded_terms = [q]

    # Check if the query matches any synonym group
    for key, synonyms in INDIAN_SYNONYM_MAP.items():
        key_words = key.split()
        if any(kw in q_lower for kw in key_words):
            # Add key synonym terms not already in query
            for syn in synonyms:
                if syn not in q_lower and len(syn.split()) <= 2:
                    expanded_terms.append(syn)

    return " ".join(expanded_terms)


def _scan_indian_pii(text: str) -> dict:
    """Scan text for Indian PII patterns and return found entities."""
    results = {
        "indian_ids": [],
        "phone_numbers": [],
        "indian_addresses": [],
    }
    if not text:
        return results

    seen = set()
    for label, pattern in INDIAN_PII_PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group().strip()
            if value and value not in seen:
                seen.add(value)
                if label in ("mobile", "phone"):
                    results["phone_numbers"].append(value)
                else:
                    results["indian_ids"].append({"type": label, "value": value})

    return results


@router.get("", response_model=dict)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    source_type: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    author: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    has_entities: Optional[str] = None,
    sort_by: str = Query("relevance", pattern="^(relevance|date|score)$"),
    deep_search: bool = Query(False, description="Enable deep search with Indian PII detection"),
    es: AsyncElasticsearch = Depends(get_es),
    current_user: CurrentUser = Depends(require_permission("search:read")),
):
    """Full-text search across all crawled content."""
    if not es:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Elasticsearch is not available",
        )

    # Expand query with Indian synonyms for better recall
    expanded_q = _expand_query_with_synonyms(q)

    # Build base fields with Indian-specific field boosts
    base_fields = [
        "title^4",                  # Title boost increased
        "content_text^2",
        "author^2",
        "site_name^1.5",           # Site name matters for credibility
        "document_type^1.5",       # Document type categorization
        "entities.emails",
        "entities.btc_addresses",
        "entities.keywords_matched",
        "entities.aadhaar",
        "entities.pan",
        "entities.voter_id",
        "entities.passport",
        "entities.upi_ids",
        "entities.phone_numbers",
        "entities.persons",
    ]

    # When deep_search is enabled, add Indian PII fields and raise minimum_should_match
    if deep_search:
        search_fields = base_fields + [
            "entities.aadhaar_numbers",
            "entities.pan_numbers",
            "entities.indian_mobiles",
            "entities.voter_ids",
            "entities.indian_passports",
            "entities.driving_license",
            "entities.gst_numbers",
            "entities.ifsc_codes",
            "entities.bank_accounts",
            "entities.credit_card_bins",
        ]
        min_should_match = "75%"  # Lowered for wider recall in deep search
    else:
        search_fields = base_fields
        min_should_match = "60%"  # Lowered for better recall with synonym expansion

    # Primary must: original query (relaxed minimum_should_match for broad recall)
    must_conditions = [
        {
            "multi_match": {
                "query": q,
                "fields": search_fields,
                "type": "most_fields",
                "fuzziness": "AUTO",
                "minimum_should_match": min_should_match,
            }
        }
    ]

    # Should: synonym-expanded query provides a boost for documents matching related terms
    should_conditions = [
        {
            "multi_match": {
                "query": expanded_q,
                "fields": search_fields,
                "type": "most_fields",
                "fuzziness": "AUTO",
                "boost": 1.5,
            }
        },
        # Severity/document type boosts
        {"term": {"scoring.severity": "critical"}},
        {"term": {"scoring.severity": "high"}},
        {"term": {"document_type": "terrorism"}},
        {"term": {"document_type": "weapons_trafficking"}},
        {"term": {"document_type": "human_trafficking"}},
        {"term": {"document_type": "data_breach"}},
        {"term": {"document_type": "cyber_espionage"}},
        {"term": {"document_type": "narcotics"}},
    ]

    # Add boosting for Indian-origin content when Indian keywords are detected
    indian_keywords = ["india", "indian", "aadhaar", "pan", "up", "delhi", "mumbai",
                       "bangalore", "kolkata", "chennai", "hdfc", "icici", "sbi",
                       "rupee", "inr", "gst", "passport", "voter"]
    if any(kw in q.lower() for kw in indian_keywords):
        should_conditions.append({"term": {"target_region": "India"}})

    # Build filter conditions
    filter_conditions = []

    if source_type:
        filter_conditions.append({"term": {"source_type": source_type}})
    if category:
        filter_conditions.append({
            "bool": {
                "should": [
                    {"term": {"document_type": category}},
                    {"term": {"analysis.classification.primary": category}},
                ]
            }
        })
    if language:
        filter_conditions.append({"term": {"language": language}})
    if author:
        filter_conditions.append({"match": {"author": author}})
    if date_from:
        filter_conditions.append({"range": {"crawl_timestamp": {"gte": date_from}}})
    if date_to:
        filter_conditions.append({"range": {"crawl_timestamp": {"lte": date_to}}})
    if has_entities:
        entity_map = {
            "btc": "entities.btc_addresses",
            "email": "entities.emails",
            "phone": "entities.phone_numbers",
            "aadhaar": "entities.aadhaar",
            "pan": "entities.pan",
            "passport": "entities.passport",
            "voter": "entities.voter_id",
            "upi": "entities.upi_ids",
        }
        entity_field = entity_map.get(has_entities)
        if entity_field:
            filter_conditions.append({"exists": {"field": entity_field}})

    # Sort
    sort_clause = []
    if sort_by == "date":
        sort_clause.append({"crawl_timestamp": {"order": "desc"}})
    elif sort_by == "score":
        sort_clause.append({"scoring.score": {"order": "desc"}})
    else:
        sort_clause.append("_score")

    es_query = {
        "bool": {
            "must": must_conditions,
        }
    }
    if should_conditions:
        es_query["bool"]["should"] = should_conditions
        es_query["bool"]["minimum_should_match"] = 0  # Don't require any should
    if filter_conditions:
        es_query["bool"]["filter"] = filter_conditions

    # Wrap in function_score for relevance boosting
    function_score = {
        "function_score": {
            "query": es_query,
            "functions": [
                {
                    "filter": {"terms": {"scoring.severity": ["critical", "high"]}},
                    "weight": 2.0,
                },
                {
                    "filter": {"terms": {"document_type": ["terrorism", "weapons_trafficking", "human_trafficking", "narcotics", "cyber_espionage"]}},
                    "weight": 1.5,
                },
            ],
            "score_mode": "multiply",
            "boost_mode": "multiply",
        }
    }

    try:
        response = await es.search(
            index="crawled_content",
            body={
                "query": function_score if sort_by == "relevance" else es_query,
                "from": (page - 1) * per_page,
                "size": per_page,
                "sort": sort_clause,
                "highlight": {
                    "fields": {
                        "content_text": {"fragment_size": 200, "number_of_fragments": 1},
                        "title": {"fragment_size": 100, "number_of_fragments": 1},
                    }
                },
                "aggs": {
                    "categories": {
                        "terms": {"field": "document_type", "size": 30}
                    },
                    "source_types": {
                        "terms": {"field": "source_type", "size": 10}
                    },
                    "languages": {
                        "terms": {"field": "language", "size": 20}
                    },
                    "severities": {
                        "terms": {"field": "scoring.severity", "size": 10}
                    },
                    "sites": {
                        "terms": {"field": "site_name", "size": 20}
                    },
                },
            },
        )

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        data = []
        for hit in hits:
            source = hit["_source"]
            highlight = hit.get("highlight", {})

            # Get snippet from highlight or content
            snippet = ""
            if highlight.get("content_text"):
                snippet = " ".join(highlight["content_text"][:200])
            elif highlight.get("title"):
                snippet = " ".join(highlight["title"])
            else:
                content = source.get("content_text", "")
                snippet = content[:300] if content else ""

            # Build matched_entities base
            matched_entities = {
                "btc_addresses": source.get("entities", {}).get("btc_addresses", []),
                "emails": source.get("entities", {}).get("emails", []),
            }

            # Build result entry
            entry = {
                "id": hit["_id"],
                "url": source.get("url", ""),
                "title": source.get("title", ""),
                "snippet": snippet,
                "author": source.get("author", ""),
                "source_type": source.get("source_type", ""),
                "site_name": source.get("site_name", ""),
                "category": source.get("document_type", ""),
                "severity_score": source.get("scoring", {}).get("score", 0),
                "language": source.get("language", ""),
                "crawled_at": source.get("crawl_timestamp", ""),
                "matched_entities": matched_entities,
                "score": hit.get("_score", 0),
            }

            # When deep_search, scan content for Indian PII and enrich response
            if deep_search:
                content_text = source.get("content_text", "")
                deep_entities = _scan_indian_pii(content_text)

                # Also scan title and snippet
                title_text = source.get("title", "")
                title_pii = _scan_indian_pii(title_text)
                for key in ("indian_ids", "phone_numbers"):
                    deep_entities[key].extend(
                        item for item in title_pii[key]
                        if item not in deep_entities[key]
                    )

                # Add to matched_entities
                matched_entities["indian_ids"] = deep_entities["indian_ids"]
                matched_entities["phone_numbers"] = deep_entities["phone_numbers"]
                matched_entities["indian_addresses"] = deep_entities["indian_addresses"]

                # Add a top-level deep_entities summary for threat scoring visibility
                entry["deep_entities"] = {
                    "indian_id_count": len(deep_entities["indian_ids"]),
                    "phone_count": len(deep_entities["phone_numbers"]),
                    "has_aadhaar": any(
                        item["type"] == "aadhaar" for item in deep_entities["indian_ids"]
                    ),
                    "has_pan": any(
                        item["type"] == "pan" for item in deep_entities["indian_ids"]
                    ),
                    "pii_detected": bool(
                        deep_entities["indian_ids"]
                        or deep_entities["phone_numbers"]
                    ),
                }
                if deep_entities["indian_ids"]:
                    entry["deep_entities"]["sample_ids"] = [
                        item["value"] for item in deep_entities["indian_ids"][:5]
                    ]

            data.append(entry)

        # Build facets from aggregations
        aggs = response.get("aggregations", {})
        facets = {
            "categories": [
                {"value": b["key"], "count": b["doc_count"]}
                for b in aggs.get("categories", {}).get("buckets", [])
            ],
            "source_types": [
                {"value": b["key"], "count": b["doc_count"]}
                for b in aggs.get("source_types", {}).get("buckets", [])
            ],
            "languages": [
                {"value": b["key"], "count": b["doc_count"]}
                for b in aggs.get("languages", {}).get("buckets", [])
            ],
            "severities": [
                {"value": b["key"], "count": b["doc_count"]}
                for b in aggs.get("severities", {}).get("buckets", [])
            ],
            "sites": [
                {"value": b["key"], "count": b["doc_count"]}
                for b in aggs.get("sites", {}).get("buckets", [])
            ],
        }

        return {
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": max(1, (total + per_page - 1) // per_page),
            },
            "facets": facets,
        }

    except Exception as e:
        logger.error("Elasticsearch search failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Search failed: {str(e)}",
        )
