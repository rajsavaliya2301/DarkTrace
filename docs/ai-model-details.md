# DarkTrace — AI / NLP Model Details

> **Version:** 1.0 | **Last Updated:** 2026-06-03

---

## 1. NLP Pipeline Overview

```
Raw Text → Language Detection → Translation (if needed)
    → Tokenization → Entity Extraction → Sentiment Analysis
    → Keyword Matching → Threat Classification → Scoring
```

The NLP pipeline processes crawled content through multiple stages to extract actionable threat intelligence.

---

## 2. Language Detection & Translation

### Supported Languages
| Language | Detection | Translation Target | Confidence Threshold |
|----------|-----------|-------------------|---------------------|
| English | Native (spaCy) | — | — |
| Hindi | fastText / langdetect | English | 0.85 |
| Russian | fastText / langdetect | English | 0.85 |
| Arabic | fastText / langdetect | English | 0.85 |
| +50 more | langdetect fallback | English | 0.70 |

### Implementation
```python
# backend/app/nlp/translator.py
class TranslatorService:
    def __init__(self):
        self.detector = language_detection()
        self.translators = {
            "hi": ArgosTranslator("hi", "en"),
            "ru": ArgosTranslator("ru", "en"),
            "ar": ArgosTranslator("ar", "en"),
        }

    async def translate(self, text: str, source_lang: str) -> str:
        if source_lang == "en":
            return text
        translator = self.translators.get(source_lang)
        if not translator:
            return text
        return translator.translate(text)
```

- Uses **argos-translate** for offline translation (no external API calls)
- **Cache** translations in Redis for 30 days to avoid reprocessing
- Falls back to Google Translate API if offline model unavailable

---

## 3. Entity Extraction

### Entities Detected
| Entity Type | Examples | spaCy Model | Sensitivity |
|-------------|----------|-------------|-------------|
| **PII** | Emails, phone numbers, SSN, addresses | Custom regex + NER | High |
| **Financial** | Credit card numbers, bank accounts | Custom regex (Luhn check) | High |
| **Crypto** | BTC addresses, ETH addresses, Monero | Custom regex + checksum | High |
| **Weapons/Contraband** | Drug names, weapons, explosives | Custom NER + keyword list | Medium |
| **Malware** | Ransomware families, C2 servers | Custom NER + threat intel feeds | Medium |
| **People** | Usernames, aliases, real names | spaCy NER (PERSON) | Low |
| **Organizations** | Groups, forums, marketplaces | spaCy NER (ORG) | Low |
| **Locations** | Cities, countries, regions | spaCy NER (GPE) | Low |

### Implementation
```python
# backend/app/nlp/entities.py
class EntityExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.pii_patterns = self._compile_patterns()

    async def extract(self, text: str) -> Dict[str, List[str]]:
        doc = self.nlp(text)
        entities = defaultdict(list)

        # spaCy NER
        for ent in doc.ents:
            if ent.label_ in self.entity_types:
                entities[ent.label_].append(ent.text)

        # Regex patterns for PII / crypto / financial
        for entity_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type].extend(matches)

        return dict(entities)
```

---

## 4. Sentiment Analysis

### Purpose
Detect planning, intent, recruitment, or coordination of illegal activities.

### Implementation
```python
# backend/app/nlp/sentiment.py
class SentimentAnalyzer:
    async def analyze(self, text: str) -> Dict:
        # Primary: VADER for English (social-media aware)
        vader_scores = self.vader.polarity_scores(text)

        # Secondary: TextBlob for polarity
        blob = TextBlob(text)
        subjectivity = blob.sentiment.subjectivity

        # Threat-specific keyword boosting
        threat_boost = self._detect_threat_language(text)

        return {
            "compound": vader_scores["compound"],
            "positive": vader_scores["pos"],
            "negative": vader_scores["neg"],
            "neutral": vader_scores["neu"],
            "subjectivity": subjectivity,
            "threat_score": self._calculate_threat_score(
                vader_scores, threat_boost
            ),
            "intent_detected": threat_boost > 0.5,
        }
```

### Sentiment Categories
| Category | Compound Score | Threat Implication |
|----------|---------------|-------------------|
| **Highly Negative** | -1.0 to -0.5 | Planning attack, recruiting |
| **Negative** | -0.5 to -0.1 | Complaint, dissatisfaction |
| **Neutral** | -0.1 to 0.1 | Informational post |
| **Positive** | 0.1 to 0.5 | Success report, boasting |
| **Highly Positive** | 0.5 to 1.0 | Celebration of attack |

### Threat Language Detection
Keywords and phrases that indicate malicious intent:
- Attack planning: "target", "take down", "DDoS", "exploit"
- Recruitment: "looking for", "need a hacker", "join us"
- Sales: "selling", "dump", "cheap", "fresh", "CC"
- Coordination: "operation", "together", "planned"

---

## 5. Threat Classification

### Classification Categories
| Category | Sub-Categories | ML Approach |
|----------|---------------|-------------|
| **Ransomware** | Listings, attacks, tools | Keyword + ML classifier |
| **Data Breach** | Dumps, leaks, credentials | Keyword + NER |
| **Financial Fraud** | Credit cards, bank fraud | Regex + pattern matching |
| **Drugs** | Sales, reviews, prices | Keyword + NER |
| **Weapons** | Firearms, explosives, 3D prints | Keyword + ML classifier |
| **Hacking Services** | Exploits, RATs, botnets | Keyword + ML classifier |
| **Counterfeit** | Documents, currencies, goods | Keyword + NER |
| **Extremism** | Propaganda, recruitment | ML classifier (content warnings apply) |

### Implementation
```python
# backend/app/nlp/classifier.py
class ThreatClassifier:
    def __init__(self):
        self.keyword_categories = self._load_keywords()
        self.ml_classifier = self._load_model()  # Optional: sklearn/TensorFlow

    async def classify(self, text: str, entities: Dict) -> List[Dict]:
        classifications = []

        # Rule-based classification (fast)
        for category, keywords in self.keyword_categories.items():
            matches = [kw for kw in keywords if kw.lower() in text.lower()]
            if matches:
                classifications.append({
                    "category": category,
                    "method": "keyword",
                    "confidence": min(len(matches) / 3, 1.0),
                    "matches": matches[:10],
                })

        # ML-based classification (if model available)
        if self.ml_classifier:
            ml_result = self.ml_classifier.predict([text])[0]
            classifications.append({
                "category": ml_result["category"],
                "method": "ml",
                "confidence": ml_result["confidence"],
                "matches": [],
            })

        return classifications
```

---

## 6. Keyword & Pattern Matching

### Watchlist Engine
```python
# backend/app/nlp/keyword_matcher.py
class KeywordMatcher:
    async def match(self, text: str, watchlists: List[Watchlist]) -> List[Match]:
        matches = []
        for watchlist in watchlists:
            for keyword in watchlist.keywords:
                if keyword.lower() in text.lower():
                    matches.append(Match(
                        watchlist_id=watchlist.id,
                        keyword=keyword,
                        position=text.lower().index(keyword.lower()),
                    ))

            for pattern in watchlist.regex_patterns:
                for match in pattern.regex.finditer(text):
                    matches.append(Match(
                        watchlist_id=watchlist.id,
                        pattern=pattern.label,
                        value=match.group(),
                        position=match.start(),
                    ))

        return matches
```

### Built-in Patterns
| Pattern Type | Regex | Example Match |
|-------------|-------|--------------|
| **Bitcoin Address** | `[13][a-km-zA-HJ-NP-Z1-9]{25,34}` | `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa` |
| **Ethereum Address** | `0x[a-fA-F0-9]{40}` | `0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18` |
| **Email** | `[\w\.-]+@[\w\.-]+\.\w+` | `user@protonmail.com` |
| **Phone** | `\+?[\d\s-]{7,15}` | `+1-555-0199` |
| **SSN** | `\d{3}-\d{2}-\d{4}` | `123-45-6789` |
| **Credit Card** | `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}` | `4111-1111-1111-1111` |

---

## 7. Threat Scoring Engine

### Scoring Formula
```
Total Score = (Classification Weight × 300)
            + (High-Value Target Weight × 200)
            + (Actor Reputation Weight × 150)
            + (Freshness Weight × 100)
            + (Sentiment Weight × 100)
            + (Keyword Match Weight × 100)
            + (Site Reputation Weight × 50)
```

Weights are configurable via `THREAT_SCORE_WEIGHTS` environment variable.

### Severity Thresholds
| Severity | Score Range | Color | Action Required |
|----------|------------|-------|-----------------|
| **Critical** | 801–1000 | 🔴 Red | Immediate investigation |
| **High** | 501–800 | 🟠 Amber | Escalate within 24 hours |
| **Medium** | 201–500 | 🟡 Yellow | Review within 72 hours |
| **Low** | 0–200 | 🟢 Green | Log for reference |

### Score Factors
| Factor | Range | Description |
|--------|-------|-------------|
| Classification | 0–300 | Ransomware = 300, Drugs = 200, General = 50 |
| High-Value Targets | 0–200 | Government, hospitals, critical infra +200 |
| Actor Reputation | 0–150 | Known threat actor (from Neo4j graph) |
| Freshness | 0–100 | Newer content scores higher (decays over 30 days) |
| Sentiment | 0–100 | High threat intent detected in sentiment |
| Keyword Matches | 0–100 | Number and severity of keyword matches |
| Site Reputation | 0–50 | Known malicious sites score higher |

---

## 8. Future Improvements

### Short-term
- [ ] Active learning loop: investigators can correct classifications
- [ ] Integration with VirusTotal, AlienVault OTX threat intel feeds
- [ ] Image analysis for marketplace product photos (weapons, drugs)
- [ ] Improved translation quality with fine-tuned models

### Medium-term
- [ ] Custom BERT-based threat classifier fine-tuned on dark web data
- [ ] Graph neural networks for actor relationship prediction
- [ ] Real-time translation pipeline with streaming support
- [ ] Automated report summarization using LLMs

### Long-term
- [ ] Predictive threat modeling (predicting attacks before they happen)
- [ ] Cross-platform identity resolution using facial recognition (where legal)
- [ ] Dark web trend prediction using time-series forecasting
- [ ] Multi-modal analysis (text + images + network patterns)
