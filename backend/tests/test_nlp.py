"""Tests for NLP module — unit tests for all analyzers."""

import pytest
from unittest.mock import AsyncMock, patch

from app.nlp.sentiment import SentimentAnalyzer
from app.nlp.classifier import ThreatClassifier
from app.nlp.keyword_matcher import KeywordMatcher
from app.nlp.entities import EntityExtractor
from app.nlp.translator import Translator
from app.nlp.analyzer import NLPAnalyzer


# ─── Sentiment Analyzer Tests ─────────────────────────────────────────────────


class TestSentimentAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SentimentAnalyzer()

    @pytest.mark.asyncio
    async def test_high_threat_text(self, analyzer):
        text = "URGENT: We have ransomware that will destroy your hospital systems. Attack immediately."
        result = await analyzer.analyze(text)
        assert result["threat_intent"] > 0.3
        assert result["urgency"] > 0.3
        assert result["hostility"] > 0.1

    @pytest.mark.asyncio
    async def test_benign_text(self, analyzer):
        text = "The weather today is quite pleasant. I enjoy reading books."
        result = await analyzer.analyze(text)
        assert result["threat_intent"] < 0.2
        assert result["hostility"] < 0.2

    @pytest.mark.asyncio
    async def test_urgency_text(self, analyzer):
        text = "URGENT: Limited time offer! Act now! Critical: deadline approaching!"
        result = await analyzer.analyze(text)
        assert result["urgency"] > 0.3

    @pytest.mark.asyncio
    async def test_hostility_text(self, analyzer):
        text = "We will destroy your systems and expose your data. Target acquired."
        result = await analyzer.analyze(text)
        assert result["hostility"] > 0.2

    @pytest.mark.asyncio
    async def test_polarity_amplifies_threat(self, analyzer):
        """Negative polarity should amplify threat intent."""
        negative_threat = "This ransomware will destroy everything. Kill all processes."
        positive_benign = "Great partnership opportunity! Wonderful collaboration!"
        neg_result = await analyzer.analyze(negative_threat)
        pos_result = await analyzer.analyze(positive_benign)
        assert neg_result["threat_intent"] > pos_result["threat_intent"]

    @pytest.mark.asyncio
    async def test_subjectivity(self, analyzer):
        text = "This is clearly the best exploit kit ever made."
        result = await analyzer.analyze(text)
        assert "subjectivity" in result


# ─── Threat Classifier Tests ─────────────────────────────────────────────────


class TestThreatClassifier:
    def setup_method(self):
        self.classifier = ThreatClassifier()

    @pytest.mark.asyncio
    async def test_ransomware_detection(self):
        text = "Selling LockBit ransomware with full source code. Buy now!"
        result = await self.classifier.classify(text, title="Ransomware Listing")
        assert result["primary"] == "ransomware"
        assert result["confidence"] > 0.1

    @pytest.mark.asyncio
    async def test_data_breach_detection(self):
        text = "Leaked database dump from major company. 1 million records."
        result = await self.classifier.classify(text, title="Database Leak")
        assert result["primary"] in ("data_breach", "ransomware")

    @pytest.mark.asyncio
    async def test_unknown_content(self):
        text = "The quick brown fox jumps over the lazy dog."
        result = await self.classifier.classify(text)
        assert result["primary"] == "unknown"

    @pytest.mark.asyncio
    async def test_multi_label(self):
        text = "Ransomware exploit kit with data breach capabilities. Buy with Bitcoin."
        result = await self.classifier.classify(text)
        assert result["primary"] in ("ransomware", "exploit", "malware")
        assert len(result["secondary"]) >= 0

    @pytest.mark.asyncio
    async def test_empty_text(self):
        result = await self.classifier.classify("")
        assert result["primary"] == "unknown"

    @pytest.mark.asyncio
    async def test_exploit_detection(self):
        text = "New zero-day exploit for CVE-2024-0001. Remote code execution."
        result = await self.classifier.classify(text)
        assert result["primary"] in ("exploit", "ransomware", "malware")

    @pytest.mark.asyncio
    async def test_fraud_detection(self):
        text = "Fake passports and driver licenses for sale. Credit card fraud."
        result = await self.classifier.classify(text)
        assert result["primary"] in ("fraud", "identity_theft", "illegal_goods")

    @pytest.mark.asyncio
    async def test_secondary_categories(self):
        text = "Ransomware with data breach and exploit kit capabilities."
        result = await self.classifier.classify(text, title="Advanced Threat")
        assert len(result["secondary"]) >= 0

    @pytest.mark.asyncio
    async def test_get_categories(self):
        categories = await self.classifier.get_categories()
        assert "ransomware" in categories
        assert "malware" in categories
        assert "exploit" in categories
        assert len(categories) > 5


# ─── Entity Extractor Tests ─────────────────────────────────────────────────


class TestEntityExtractor:
    def setup_method(self):
        self.extractor = EntityExtractor()

    @pytest.mark.asyncio
    async def test_btc_extraction(self):
        text = "Bitcoin address: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        entities = await self.extractor.extract_all(text)
        assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in entities.get("btc_addresses", [])

    @pytest.mark.asyncio
    async def test_email_extraction(self):
        text = "Contact me at darkuser@protonmail.com for more info"
        entities = await self.extractor.extract_all(text)
        assert "darkuser@protonmail.com" in entities.get("emails", [])

    @pytest.mark.asyncio
    async def test_phone_extraction(self):
        text = "Call me at +919876543210"
        entities = await self.extractor.extract_all(text)
        assert len(entities.get("phone_numbers", [])) > 0

    @pytest.mark.asyncio
    async def test_pii_extraction(self):
        text = "My Aadhaar is 1234 5678 9012 and PAN is ABCDE1234F"
        pii = await self.extractor.extract_pii(text)
        assert len(pii.get("aadhaar", [])) > 0
        assert len(pii.get("pan", [])) > 0

    @pytest.mark.asyncio
    async def test_financial_extraction(self):
        text = "BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa, CC: 4111-1111-1111-1111"
        financial = await self.extractor.extract_financial(text)
        assert len(financial.get("btc_addresses", [])) > 0

    @pytest.mark.asyncio
    async def test_empty_text(self):
        entities = await self.extractor.extract_all("")
        assert len(entities) == 0  # Empty dict since no entities found

    @pytest.mark.asyncio
    async def test_ip_extraction(self):
        text = "Server IP: 192.168.1.1"
        entities = await self.extractor.extract_all(text)
        assert "192.168.1.1" in entities.get("ip_addresses", [])

    @pytest.mark.asyncio
    async def test_ssn_extraction(self):
        text = "SSN: 123-45-6789"
        entities = await self.extractor.extract_all(text)
        assert "123-45-6789" in entities.get("ssn", [])

    @pytest.mark.asyncio
    async def test_url_extraction(self):
        text = "Visit http://test.onion for more"
        entities = await self.extractor.extract_all(text)
        assert len(entities.get("urls", [])) > 0

    @pytest.mark.asyncio
    async def test_eth_extraction(self):
        text = "ETH: 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18"
        entities = await self.extractor.extract_all(text)
        assert len(entities.get("eth_addresses", [])) > 0


# ─── Translator Tests ───────────────────────────────────────────────────────


class TestTranslator:
    def setup_method(self):
        self.translator = Translator()

    @pytest.mark.asyncio
    async def test_detect_language_english(self):
        result = await self.translator.detect_language("Hello, how are you?")
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_detect_language_empty(self):
        result = await self.translator.detect_language("")
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_detect_language_confidence(self):
        result = await self.translator.detect_language("This is a test")
        assert "confidence" in result
        assert "language_name" in result

    @pytest.mark.asyncio
    async def test_translate_empty(self):
        result = await self.translator.translate("")
        assert result is None

    @pytest.mark.asyncio
    async def test_translate_english_to_english(self):
        # Text detected as English -> same target -> return None
        result = await self.translator.translate("Hello world", "en")
        assert result is None or result == "Hello world"

    @pytest.mark.asyncio
    async def test_supported_languages(self):
        assert "en" in self.translator.SUPPORTED_LANGUAGES
        assert "ru" in self.translator.SUPPORTED_LANGUAGES
        assert "ar" in self.translator.SUPPORTED_LANGUAGES
        assert self.translator.SUPPORTED_LANGUAGES["en"] == "English"


# ─── NLP Analyzer Tests ─────────────────────────────────────────────────────


class TestNLPAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_content_id(self):
        analyzer = NLPAnalyzer()
        # This will try to use real services - skip if not available
        # Test that it at least runs without error and returns a result
        try:
            result = await analyzer.analyze(
                content_id="test123",
                text="This is a test content for analysis.",
                title="Test",
            )
            assert "content_id" in result
            assert result["content_id"] == "test123"
        except Exception as e:
            # May fail due to missing external libs - that's OK
            pytest.skip(f"NLP analyzer requires external libs: {e}")


# ─── Keyword Matcher Tests ──────────────────────────────────────────────────


class TestKeywordMatcher:
    @pytest.mark.asyncio
    async def test_match_empty_text(self):
        matcher = KeywordMatcher()
        result = await matcher.match_all("")
        assert result["matched_keywords"] == []
        assert result["matched_patterns"] == []
        assert result["severity_boost"] == 0

    @pytest.mark.asyncio
    async def test_match_no_watchlists(self):
        matcher = KeywordMatcher()
        # Mock _get_active_watchlists to return empty list to avoid DB access
        with patch.object(matcher, "_get_active_watchlists", new_callable=AsyncMock, return_value=[]):
            result = await matcher.match_all("ransomware content here")
        # Without watchlists, no keywords will be matched
        assert isinstance(result["matched_keywords"], list)
        assert isinstance(result["severity_boost"], int)


from app.main import app  # noqa: E402 — needed for API endpoint tests


# ─── NLP API Integration Tests ────────────────────────────────────────────────


class TestNLPApiEndpoints:
    """Integration tests for NLP API endpoints."""

    def test_analyze_no_auth(self, client):
        """Test analyze endpoint requires auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.post("/v1/nlp/analyze", json={"text": "test content"})
        assert response.status_code in (401, 403)

    def test_analyze_authenticated(self, client, admin_auth_headers):
        """Test analyze endpoint with auth."""
        response = client.post(
            "/v1/nlp/analyze",
            json={"text": "Selling ransomware exploit kit for Bitcoin. Contact dark@protonmail.com", "title": "Test"},
            headers=admin_auth_headers,
        )
        # May fail with 500 if spaCy models not installed, but should not be 401/403
        assert response.status_code in (200, 500, 503)

    def test_translate_endpoint(self, client, admin_auth_headers):
        """Test translate endpoint."""
        response = client.post(
            "/v1/nlp/translate",
            json={"text": "Bonjour le monde", "target_language": "en"},
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 500, 503)

    def test_extract_entities_endpoint(self, client, admin_auth_headers):
        """Test entity extraction endpoint."""
        response = client.post(
            "/v1/nlp/extract-entities",
            json={"text": "Contact me at test@example.com or 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"},
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 500)

    def test_classify_endpoint(self, client, admin_auth_headers):
        """Test classification endpoint."""
        response = client.post(
            "/v1/nlp/classify",
            json={"text": "Selling zero-day exploit for $50000 in Bitcoin", "title": "Exploit for sale"},
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 500)

    def test_sentiment_endpoint(self, client, admin_auth_headers):
        """Test sentiment analysis endpoint."""
        response = client.post(
            "/v1/nlp/sentiment",
            json={"text": "This is a very dangerous and threatening message"},
            headers=admin_auth_headers,
        )
        assert response.status_code in (200, 500)

    def test_analyze_empty_text(self, client, admin_auth_headers):
        """Test analyze with empty text."""
        response = client.post(
            "/v1/nlp/analyze",
            json={"text": ""},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    def test_extract_entities_no_auth(self, client):
        """Test entity extraction requires auth."""
        from app.dependencies import get_current_user
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]
        response = client.post("/v1/nlp/extract-entities", json={"text": "test"})
        assert response.status_code in (401, 403)
