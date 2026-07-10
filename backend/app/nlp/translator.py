"""Multi-language translation module with caching."""

import hashlib
import logging
import re
from typing import Dict, Optional

from app.config import get_settings
from app.database import get_redis

logger = logging.getLogger(__name__)


class Translator:
    """Translate text between languages using offline model or API fallback."""

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "ru": "Russian",
        "ar": "Arabic",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "zh": "Chinese (Simplified)",
        "pt": "Portuguese",
        "bn": "Bengali",
        "ur": "Urdu",
        "pa": "Punjabi",
        "mr": "Marathi",
        "te": "Telugu",
        "ta": "Tamil",
        "ja": "Japanese",
        "ko": "Korean",
        "tr": "Turkish",
        "vi": "Vietnamese",
        "th": "Thai",
        "id": "Indonesian",
        "ms": "Malay",
        "fa": "Persian (Farsi)",
        "ps": "Pashto",
        "ku": "Kurdish",
        "sd": "Sindhi",
        "gu": "Gujarati",
        "kn": "Kannada",
        "ml": "Malayalam",
        "or": "Odia",
        "as": "Assamese",
        "si": "Sinhala",
        "ne": "Nepali",
        "my": "Burmese",
        "km": "Khmer",
        "lo": "Lao",
        "mn": "Mongolian",
        "ug": "Uyghur",
        "bo": "Tibetan",
        "dz": "Dzongkha",
        "uk": "Ukrainian",
        "pl": "Polish",
        "cs": "Czech",
        "nl": "Dutch",
        "it": "Italian",
        "ro": "Romanian",
        "hu": "Hungarian",
        "el": "Greek",
        "he": "Hebrew",
        "am": "Amharic",
        "sw": "Swahili",
    }

    # Language codes that can be detected
    DETECTABLE_LANGUAGES = [
        "en", "hi", "ru", "ar", "es", "fr", "de", "zh", "pt", "bn", "ur", "pa", "mr", "te", "ta",
        "ja", "ko", "tr", "vi", "th", "id", "ms", "fa", "ps", "ku", "sd", "gu", "kn", "ml", "or",
        "as", "si", "ne", "my", "km", "lo", "mn", "ug", "bo", "dz", "uk", "pl", "cs", "nl", "it",
        "ro", "hu", "el", "he", "am", "sw",
    ]

    def __init__(self):
        self._translator = None
        self._model_loaded = False

    async def _ensure_loaded(self):
        """Lazy-load the translation model."""
        if not self._model_loaded:
            try:
                # Try argos-translate first (offline)
                import argostranslate.package
                import argostranslate.translate

                from_code = "en"
                # Install all language pairs from English (offline)
                language_pairs = [
                    "en-hi", "en-ru", "en-ar", "en-es", "en-fr", "en-de",
                    "en-zh", "en-pt", "en-bn", "en-ur", "en-pa", "en-mr",
                    "en-te", "en-ta", "en-ja", "en-ko", "en-tr", "en-vi",
                    "en-th", "en-id", "en-fa", "en-ps", "en-ku", "en-sd",
                    "en-gu", "en-kn", "en-ml", "en-or", "en-si", "en-ne",
                    "en-my", "en-km", "en-uk", "en-pl", "en-cs", "en-nl",
                    "en-it", "en-ro", "en-hu", "en-el", "en-he",
                ]
                installed_packages = []
                for pair in language_pairs:
                    try:
                        argostranslate.package.install_package(pair)
                        installed_packages.append(pair)
                    except Exception as e:
                        logger.debug("Failed to install argos package %s: %s", pair, e)

                self._translator = argostranslate.translate
                self._model_loaded = True
                logger.info("Installed %d/%d argos-translate language pairs",
                            len(installed_packages), len(language_pairs))
            except ImportError:
                logger.warning("argos-translate not available. Using fallback.")
                self._model_loaded = True
            except Exception as e:
                logger.warning("argos-translate init failed: %s. Using fallback.", e)
                self._model_loaded = True

    async def detect_language(self, text: str) -> dict:
        """Detect the language of the given text."""
        if not text or not text.strip():
            return {"language": "en", "confidence": 1.0, "language_name": "English"}

        try:
            from langdetect import detect, detect_langs
            lang = detect(text)
            confidence = 1.0
            try:
                langs = detect_langs(text)
                if langs:
                    confidence = langs[0].prob
            except Exception:
                pass
            lang_name = self.SUPPORTED_LANGUAGES.get(lang, lang)
            return {"language": lang, "confidence": round(confidence, 4), "language_name": lang_name}
        except ImportError:
            logger.debug("langdetect not available, defaulting to en")
            return {"language": "en", "confidence": 1.0, "language_name": "English"}
        except Exception as e:
            logger.debug("Language detection failed: %s", e)
            return {"language": "en", "confidence": 0.5, "language_name": "English"}

    async def detect_darkweb_variants(self, text: str) -> Dict:
        """Detect dark web language variants, slang, and code-mixing."""
        if not text:
            return {"variant": "standard", "confidence": 1.0}

        # Features for detection
        features = {
            "has_cyrillic": bool(re.search(r'[а-яА-ЯёЁ]', text)),
            "has_arabic_script": bool(re.search(r'[\u0600-\u06FF\u0750-\u077F]', text)),
            "has_devanagari": bool(re.search(r'[\u0900-\u097F]', text)),
            "has_chinese": bool(re.search(r'[\u4e00-\u9fff]', text)),
            "has_korean": bool(re.search(r'[\uAC00-\uD7AF]', text)),
            "has_thai": bool(re.search(r'[\u0E00-\u0E7F]', text)),
            "has_emoji_heavy": len(re.findall(r'[\U0001F300-\U0001FAFF]', text)) > 3,
            "has_leetspeak": bool(re.search(r'[4137$@]', text)),
            "has_base64_blocks": bool(re.search(r'[A-Za-z0-9+/]{40,}={0,2}', text)),
            "has_pgp_blocks": bool(re.search(r'-----BEGIN PGP', text)),
        }

        # Detect code-mixing (multiple scripts in same text)
        scripts_detected = sum(1 for v in features.values() if isinstance(v, bool) and v)

        return {
            "variant": "code_mixed" if scripts_detected > 2 else "standard",
            "features": features,
            "needs_transliteration": features.get("has_cyrillic", False) or features.get("has_arabic_script", False),
        }

    async def preprocess_darkweb_text(self, text: str) -> str:
        """Preprocess dark web text for better translation/analysis."""
        if not text:
            return text

        # Remove PGP blocks (they confuse translation models)
        text = re.sub(r'-----BEGIN PGP.*?-----END PGP-----', '[PGP BLOCK]', text, flags=re.DOTALL)

        # Remove base64-encoded blobs
        text = re.sub(r'[A-Za-z0-9+/]{100,}={0,2}', '[BINARY DATA]', text)

        # Normalize leetspeak (common in hacker forums)
        leet_map = {
            '4': 'a', '@': 'a', '3': 'e', '1': 'i', '0': 'o',
            '5': 's', '$': 's', '7': 't', '8': 'b', '2': 'z',
        }
        # Only apply to words that look leetspeak (mix of letters and numbers)
        words = text.split()
        normalized_words = []
        for word in words:
            if re.search(r'[a-zA-Z]', word) and re.search(r'[0-9]', word) and len(word) < 15:
                for leet_char, real_char in leet_map.items():
                    word = word.replace(leet_char, real_char)
            normalized_words.append(word)
        text = ' '.join(normalized_words)

        # Remove repeated URLs to reduce noise
        text = re.sub(r'(https?://\S+\s?){3,}', '[MULTIPLE URLS] ', text)

        return text

    async def translate(self, text: str, target_lang: str = "en") -> Optional[str]:
        """Translate text to target language. Returns None if not needed or fails."""
        if not text or not text.strip():
            return None

        # Check if already english
        detected = await self.detect_language(text)
        if detected["language"] == target_lang:
            return None

        # Check cache
        cache_key = f"trans:{hashlib.sha256(text.encode()).hexdigest()}:{target_lang}"
        try:
            redis = await get_redis()
            cached = await redis.get(cache_key)
            if cached:
                logger.debug("Translation cache hit")
                return cached
        except Exception:
            pass

        # Perform translation
        translated = await self._translate_internal(text, detected["language"], target_lang)

        # Cache result
        if translated:
            try:
                settings = get_settings()
                redis = await get_redis()
                await redis.setex(cache_key, settings.TRANSLATION_CACHE_TTL, translated)
            except Exception:
                pass

        return translated

    async def _translate_internal(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Internal translation logic with fallback chain."""
        if source_lang == target_lang:
            return text

        # Method 1: argos-translate (offline)
        if self._translator:
            try:
                translated = self._translator.translation(text, source_lang, target_lang)
                if translated and translated.strip():
                    return translated
            except Exception as e:
                logger.debug("argos-translate failed: %s", e)

        # Method 2: googletrans (online fallback)
        try:
            from googletrans import Translator as GoogleTranslator
            gt = GoogleTranslator()
            result = await gt.translate(text, src=source_lang, dest=target_lang)
            if result and result.text:
                return result.text
        except ImportError:
            logger.debug("googletrans not available")
        except Exception as e:
            logger.debug("googletrans failed: %s", e)

        logger.warning("All translation methods failed for %s -> %s", source_lang, target_lang)
        return None


# Singleton
_translator: Optional[Translator] = None


async def get_translator() -> Translator:
    """Get or create the singleton translator."""
    global _translator
    if _translator is None:
        _translator = Translator()
        await _translator._ensure_loaded()
    return _translator
