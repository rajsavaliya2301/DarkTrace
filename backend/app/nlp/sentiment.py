"""Sentiment and intent analysis for threat detection."""

import logging
import re
from typing import Dict, Optional
from textblob import TextBlob

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment, threat intent, hostility, and urgency in text."""

    def __init__(self):
        self._threat_keywords = {
            "high_threat": [
                "kill", "attack", "exploit", "ransomware", "malware",
                "trojan", "stealer", "ddos", "breach", "leak",
                "compromise", "infiltrate", "hack", "crack", "bypass",
                "zero-day", "0day", "backdoor", "botnet", "shell",
                "inject", "payload", "virus", "worm", "rootkit",
                "keylogger", "spyware", "phish", "fraud", "scam",
                "terror", "bomb", "ied", "massacre", "shooting",
                "weaponize", "militant", "insurgent", "jihad",
                # Chinese cyber threat keywords
                "网络攻击", "木马", "病毒", "漏洞", "后门", "入侵",
                "钓鱼", "间谍", "窃密", "破坏", "瘫痪", "渗透",
                "黑客", "网络战", "数据泄露", "网络间谍",
                # Urdu threat keywords
                "حملہ", "دھماکہ", "نقصان", "تباہی", "ہیکنگ",
                "نفوذ", "دراندازی", "چوری", "نقصان پہنچانا",
                # Russian threat keywords
                "атака", "взлом", "утечка", "шпионаж", "вирус",
                "троян", "червь", "вредонос", "хищение", "разрушение",
                # Arabic threat keywords
                "هجوم", "ثغرة", "اختراق", "تسريب", "فايروس",
                "برمجية خبيثة", "هندسة اجتماعية", "تصيد",
            ],
            "urgency": [
                "urgent", "immediate", "asap", "critical", "emergency",
                "hurry", "limited time", "offer expires", "act now",
                "deadline", "warning", "alert", "attention required",
                "imminent", "today only", "flash", "breaking", "urgent action",
            ],
            "hostility": [
                "destroy", "damage", "ruin", "target", "victim",
                "take down", "shut down", "expose", "dump",
                "release", "publish", "humiliate", "embarrass",
                "annihilate", "exterminate", "wipe out", "slaughter",
                "massacre", "eliminate", "eradicate", "crush",
                "devastate", "sabotage", "disrupt", "disable",
            ],
            "cooperation": [
                "partnership", "collaborate", "joint", "team",
                "help", "assist", "support", "cooperation",
                "affiliate", "referral", "commission",
                "brotherhood", "alliance", "network", "solidarity",
                "united", "together", "collective", "fraternity",
            ],
            "extremism": [
                "jihad", "martyrdom", "shaheed", "caliphate", "khilafah",
                "infidel", "kafir", "apostate", "murtad", "crusader",
                "holy war", "religious war", "fatwa", "declaration of war",
                "lone wolf", "inspired attack", "lone mujahid",
                "establish sharia", "islamic rule", "islamic state",
                "global jihad", "armed jihad", "defensive jihad",
                "offensive jihad", "martyr", "shahid", "operation martyrdom",
                "revenge", "retaliation", "blood for blood", "eye for an eye",
                "take up arms", "rise up", "overthrow", "revolution",
                "purification", "cleansing", "ethnic cleansing",
            ],
            "radicalization": [
                "join the fight", "answer the call", "come to jihad",
                "brother in islam", "sister in islam", "the oppressed",
                "defend the ummah", "protect the ummah", "ummah",
                "wake up", "open your eyes", "brainwashed", "propaganda",
                "recruitment video", "training camp", "online radicalization",
                "telegram channel", "encrypted messaging", "secret group",
                "guide", "manual", "how to", "learn to fight",
                "become a fighter", "join the ranks", "swear allegiance",
                "bayah", "bai'ah", "oath of allegiance", "pledge",
                "emir", "commander of the faithful", "ameer",
                "hijrah", "migration", "land of jihad", "front lines",
                # Urdu radicalization keywords
                "شامل ہوں", "جہاد میں شامل ہوں", "اسلام میں بھائی", "امت کی حفاظت",
                "بیدار ہو", "پروپیگنڈا", "تربیتی کیمپ", "آن لائن ریڈیکلائزیشن",
                "خفیہ گروپ", "رہنما", "رہنمائی", "لڑنا سیکھیں",
                "بیعت", "امیر", "ہجرت", "جہاد کی سرزمین", "محاذ",
                # Arabic radicalization keywords
                "انضم للقتال", "أجب النداء", "تعال للجهاد", "أخ في الإسلام",
                "أخت في الإسلام", "المظلومون", "دافع عن الأمة", "استيقظ",
                "افتح عينيك", "دعاية", "معسكر تدريب", "التطرف عبر الإنترنت",
                "قناة تليجرام", "مجموعة سرية", "كتيب", "دليل", "كيف تقاتل",
                "بايع", "أمير", "هجرة", "أرض الجهاد", "جبهات القتال",
            ],
        }
        self._loaded = True

    async def analyze(self, text: str) -> Dict[str, float]:
        """Analyze text and return sentiment/threat dimensions (0.0–1.0)."""
        if not text or not text.strip():
            return {
                "threat_intent": 0.0,
                "hostility": 0.0,
                "urgency": 0.0,
                "cooperation": 0.0,
                "polarity": 0.0,
                "subjectivity": 0.0,
            }

        text_lower = text.lower()

        # Keyword-based scoring
        word_count = len(text_lower.split())
        if word_count == 0:
            word_count = 1

        threat_intent = self._score_keywords(text_lower, "high_threat", word_count)
        urgency = self._score_keywords(text_lower, "urgency", word_count)
        hostility = self._score_keywords(text_lower, "hostility", word_count)
        cooperation = self._score_keywords(text_lower, "cooperation", word_count)

        # TextBlob polarity and subjectivity
        polarity = 0.0
        subjectivity = 0.0
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1.0 to 1.0
            subjectivity = blob.sentiment.subjectivity  # 0.0 to 1.0
        except Exception as e:
            logger.warning("TextBlob analysis failed: %s", e)

        # Normalize threat intent based on polarity
        # Negative polarity amplifies threat intent
        if polarity < -0.2:
            threat_intent = min(1.0, threat_intent * 1.3)
        elif polarity > 0.3:
            threat_intent = max(0.0, threat_intent * 0.7)

        return {
            "threat_intent": round(min(1.0, threat_intent), 4),
            "hostility": round(min(1.0, hostility), 4),
            "urgency": round(min(1.0, urgency), 4),
            "cooperation": round(min(1.0, cooperation), 4),
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
        }

    def _score_keywords(self, text_lower: str, category: str, word_count: int) -> float:
        """Score text for a keyword category."""
        keywords = self._threat_keywords.get(category, [])
        if not keywords:
            return 0.0

        matches = 0
        for kw in keywords:
            # Use word boundary for single words, simple substring for phrases
            if " " in kw:
                if kw in text_lower:
                    matches += 1
            else:
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches += len(re.findall(pattern, text_lower, re.IGNORECASE))

        if matches == 0:
            return 0.0

        # Score based on density: 3+ matches in 100 words = high threat
        density = matches / max(word_count, 1) * 100
        score = min(1.0, density / 5.0)  # 5% density = max score
        return score


# Singleton
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


async def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create the singleton sentiment analyzer."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
