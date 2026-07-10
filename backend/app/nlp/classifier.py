"""Threat content classification — categorizes content into threat types."""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ThreatClassifier:
    """Classifies content into threat categories with confidence scores."""

    CATEGORIES = [
        "ransomware",
        "malware",
        "exploit",
        "data_breach",
        "fraud",
        "illegal_goods",
        "services",
        "intelligence",
        "hacktivism",
        "carding",
        "identity_theft",
        "drugs",
        "weapons",
        "terrorism",
        "extremism",
        "weapons_trafficking",
        "human_trafficking",
        "narcotics",
        "cyber_espionage",
    ]

    # Keywords per category with weights
    CATEGORY_KEYWORDS = {
        "ransomware": {
            "keywords": [
                "ransomware", "lockbit", "blackcat", "alphv", "hive", "conti",
                "revil", "babuk", "lorenz", "clop", "ransom", "decryptor",
                "ransom note", "ransom demand", "bitcoin ransom", "ransomware as a service",
                "raas", "double extortion", "leak site", "ransomware gang",
                "ransomware group", "ransomware affiliate", "lockbit 3.0", "bashlock",
            ],
            "weight": 0.3,
        },
        "malware": {
            "keywords": [
                "malware", "trojan", "virus", "worm", "rootkit", "keylogger",
                "spyware", "banker", "stealer", "rat", "remote access trojan",
                "botnet", "loader", "dropper", "backdoor", "infostealer",
                "banking trojan", "mobile malware", "android malware", "ios malware",
                "pegasus", "predator", "spyware", "worm", "malspam",
            ],
            "weight": 0.2,
        },
        "exploit": {
            "keywords": [
                "exploit", "zero-day", "0day", "vulnerability", "cve", "remote code execution",
                "rce", "sql injection", "xss", "buffer overflow", "privilege escalation",
                "poc", "proof of concept", "exploit kit", "weaponization",
                "exploit database", "metasploit", "cve-202", "cve-2024", "cve-2025", "cve-2026",
                "log4shell", "log4j", "shellshock", "eternalblue", "printnightmare",
            ],
            "weight": 0.25,
        },
        "data_breach": {
            "keywords": [
                "data breach", "leak", "leaked", "database dump", "credential dump",
                "breach", "exposed data", "customer data", "user data", "compromised",
                "leaked database", "dark web leak", "breach forum",
                "data leak", "personal information", "pii leak", "records leaked",
                "breach alert", "breach notification", "breach forum", "raidforum",
                "breached", "breachforums", "exploit.in", "cracked.io", "nulled",
            ],
            "weight": 0.2,
        },
        "fraud": {
            "keywords": [
                "fraud", "scam", "phishing", "carding", "fake identity", "fake documents",
                "passport", "driver license", "credit card", "doxxing", "dox",
                "social engineering", "identity theft", "bank fraud",
                "advance fee", "investment scam", "crypto scam", "ponzi", "pyramid scheme",
                "spear phishing", "whaling", "CEO fraud", "invoice fraud", "payment fraud",
            ],
            "weight": 0.2,
        },
        "illegal_goods": {
            "keywords": [
                "counterfeit", "fake money", "fake bills", "stolen goods",
                "counterfeit goods", "fake documents", "fake passport",
                "replica", "knockoff", "fake id", "forged documents",
                "stolen merchandise", "hacked goods", "fraudulent documents",
            ],
            "weight": 0.15,
        },
        "services": {
            "keywords": [
                "ddos service", "stresser", "booter", "bulletproof hosting", "vpn service",
                "email spam", "sms spam", "account creation", "verification service",
                "money laundering", "mixing service", "tumbler", "cash out",
                "bulletproof", "hosting service", "smtp service", "email bomber",
                "sms bomber", "phone verification", "account verification",
            ],
            "weight": 0.15,
        },
        "intelligence": {
            "keywords": [
                "intelligence", "threat actor", "apt", "cyber attack", "cyber operation",
                "military", "government", "intel", "reconnaissance", "surveillance",
                "spy", "espionage", "information gathering", "threat intelligence",
                "apt group", "apt28", "apt29", "fancy bear", "cozy bear", "lazarus",
                "kimsuky", "tajmahal", "apt-c", "state sponsored", "state actor",
            ],
            "weight": 0.2,
        },
        "carding": {
            "keywords": [
                "carding", "ccv", "cvv", "dumps", "fullz", "credit card",
                "debit card", "cardable", "bin", "card not present", "carding forum",
                "card dumps", "track 1", "track 2", "dumpshop", "cardshop",
                "credit card numbers", "card verification", "cvv2", "valid cc",
                "credit card fraud", "carding method", "carding tutorial",
            ],
            "weight": 0.25,
        },
        "hacktivism": {
            "keywords": [
                "hacktivism", "defaced", "defacement", "anonymous", "operation",
                "protest", "political", "activist", "hacked by", "take down",
                "opindia", "opisis", "anonymous india", "legion", "cyber protest",
                "hacktivist", "anonymous operation", "free speech", "censorship",
            ],
            "weight": 0.15,
        },
        "terrorism": {
            "keywords": [
                "terrorism", "terrorist", "terror", "bomb", "ied", "explosive",
                "suicide attack", "bombing", "mass casualty", "mass shooting",
                "jihad", "mujahideen", "mujahid", "shaheed", "martyrdom operation",
                "isis", "islamic state", "al qaeda", "al-qaeda", "taliban",
                "lashkar e taiba", "let", "jaish e mohammad", "jem",
                "hizb-ul-mujahideen", "hizbul", "huJI", "harkat-ul-jihad",
                "boko haram", "al shabaab", "hesbollah", "hezbollah", "hamas",
                "pkk", "separatist", "insurgency", "insurgent", "guerrilla",
                "car bomb", "suicide vest", "suicide bomber", "lone wolf",
                "radicalization", "recruitment", "foreign fighter", "terror financing",
                "hawala", "terror funding", "weapon of mass destruction", "wmd",
                "biological weapon", "chemical weapon", "dirty bomb", "radiological",
                "nexus", "naxal", "maoist", "left wing extremism", "lwe",
                "आतंकवाद", "आतंकवादी", "आतंकी", "हमला", "बम", "विस्फोट",
                "आईईडी", "आत्मघाती", "जिहाद", "शहीद", "मुजाहिद",
                "इस्लामिक स्टेट", "अल कायदा", "लश्कर", "तालिबान",
                # Urdu keywords for Pakistan-linked terrorism
                "دہشت گردی", "دہشت گرد", "حملہ", "بم", "دھماکہ",
                "جہاد", "مجاہد", "مجاہدین", "شہید", "خودکش حملہ",
                "القاعدہ", "طالبان", "داعش", "اسلامی ریاست", "لشکر",
                "جیش محمد", "تحریک طالبان", "سپاہ صحابہ", "اجود",
                # Arabic keywords for ISIS/Al-Qaeda content
                "إرهاب", "إرهابي", "هجوم", "قنبلة", "انفجار",
                "جهاد", "مجاهد", "شهيد", "عملية استشهادية",
                "تنظيم الدولة", "داعش", "القاعدة", "طالبان",
                "تفجير انتحاري", "حزام ناسف", "عبوة ناسفة", "سيارة مفخخة",
                "الخلافة", "أمير المؤمنين", "الجهاد في سبيل الله",
                "هجوم مسلح", "كمين", "تصفية", "اغتيال", "خطف",
                # Pashto keywords for Afghanistan/Pakistan region
                "ترهګري", "برید", "چاودنه", "جهاد", "مجاهد", "طالبان",
                "شهید", "خودکش برید", "القاعده", "داعش",
                # Persian/Farsi keywords for Iran-linked content
                "تروریسم", "حمله", "بمب", "انفجار", "جهاد", "شهید",
                "القاعده", "طالبان", "داعش", "حزب‌الله", "سپاه قدس",
                # Bengali keywords for Bangladesh/NE India region
                "সন্ত্রাসবাদ", "সন্ত্রাসী", "হামলা", "বোমা", "বিস্ফোরণ",
                "জিহাদ", "মুজাহিদ", "শহীদ", "আত্মঘাতী হামলা",
                "আইএসআইএস", "আল কায়েদা", "তালিবান",
            ],
            "weight": 0.35,
        },
        "extremism": {
            "keywords": [
                "extremism", "extremist", "radical", "radicalization", "fundamentalist",
                "far right", "far left", "white supremacist", "neo nazi", "nazi",
                "islamist", "islamist extremism", "jihadist", "jihadi",
                "religious extremism", "political extremism", "violent extremism",
                "radical islam", "islamic extremism", "hate speech", "incitement",
                "communal violence", "sectarian", "sectarian violence", "riots",
                "ethnic cleansing", "genocide", "hate crime", "xenophobia",
                "ultra nationalist", "hindutva extremism", "khalistan", "separatist movement",
                "insurgency", "subversive", "anti national", "anti india",
                "naxalite", "maoist insurgent", "northeast insurgency", "ul-fa",
                "nscn-im", "prepak", "kangleipak", "bodo extremism", "ndfb",
                # Urdu keywords
                "انتہا پسندی", "شدت پسندی", "بنیاد پرستی", "مذہبی انتہا پسندی",
                "فرقہ واریت", "نفرت", "تشدد", "فکری منڈی",
                # Arabic keywords
                "تطرف", "تشدد", "طائفية", "كراهية", "تحريض",
                "إثارة الفتنة", "تعصب", "تكفير", "غلو",
                # Chinese keywords for Uyghur/Xinjiang extremism
                "极端主义", "恐怖主义", "分裂主义", "暴力恐怖", "宗教极端",
                "东突厥斯坦", "东伊运", "维吾尔", "圣战",
                # Bengali keywords
                "চরমপন্থা", "উগ্রবাদ", "ঘৃণা", "সাম্প্রদায়িক", "উসকানি",
                # Persian/Farsi keywords
                "افراط‌گرایی", "تندروی", "نفرت", "تحریک", "تعصب",
            ],
            "weight": 0.3,
        },
        "weapons_trafficking": {
            "keywords": [
                "weapons trafficking", "arms trafficking", "arms dealer", "gun running",
                "illegal weapons", "illicit arms", "smuggling weapons", "firearm",
                "assault rifle", "submachine gun", "machine gun", "pistol", "revolver",
                "ak-47", "ak47", "ar-15", "ar15", "shotgun", "rifle", "carbine",
                "ammunition", "ammo", "bullets", "cartridges", "grenade", "explosive",
                "rocket launcher", "rpg", "shoulder fired", "mortar", "landmine",
                "rifle", "handgun", "semi automatic", "fully automatic", "silencer",
                "suppressor", "gun permit", "arms license", "weapon smuggler",
                "nepal route", "arms cache", "weapons cache", "weapons haul",
                # Urdu keywords for arms trafficking
                "اسلحہ فروشی", "اسلحہ اسمگلنگ", "غیر قانونی اسلحہ", "اسلحہ ڈیلر",
                "بندوق", "پستول", "رائفل", "گولیاں", "بارود",
                "دھماکہ خیز مواد", "راکٹ لانچر", "آر پی جی", "جنریٹر",
                # Arabic keywords
                "اتجار بالأسلحة", "تهريب الأسلحة", "أسلحة غير قانونية", "تاجر أسلحة",
                "بندقية", "مسدس", "رصاص", "ذخيرة", "متفجرات",
                "قاذف صواريخ", "أر بي جي", "سلاح ناري",
                # Pashto keywords
                "وسله پلورنه", "غیرقانوني وسله", "تپانچه", "گولي", "بارود",
                # Persian/Farsi keywords
                "قاچاق اسلحه", "اسلحه غیرمجاز", "جنگ‌افزار", "تیراندازی",
                "فشنگ", "مهمات", "مواد منفجره",
            ],
            "weight": 0.3,
        },
        "human_trafficking": {
            "keywords": [
                "human trafficking", "trafficking", "forced labor", "sex trafficking",
                "child trafficking", "human smuggling", "people smuggling",
                "bonded labor", "child labor", "forced marriage", "sexual exploitation",
                "trafficked women", "trafficked children", "modern slavery", "slave trade",
                "organ trafficking", "kidnapping", "abduction", "missing persons",
                "fraudulent recruitment", "labor exploitation", "trafficking ring",
                "brothel", "forced prostitution", "child exploitation", "coyote",
                # Arabic keywords
                "اتجار بالبشر", "عمالة قسرية", "اتجار جنسي", "اتجار بالأطفال",
                "تهريب البشر", "رق", "استغلال جنسي", "خطف",
                # Bengali keywords for India-Bangladesh trafficking route
                "মানব পাচার", "যৌন পাচার", "শিশু পাচার", "দাসত্ব",
                "জোরপূর্বক শ্রম", "পাচারকারী চক্র", "উদ্ধার",
                # Urdu keywords
                "انسانی سمگلنگ", "جبری مشقت", "جنسی استحصال", "بچوں کی سمگلنگ",
                "غلامی", "اغوا", "بھتہ خوری",
                # Hindi keywords for domestic trafficking
                "मानव तस्करी", "यौन शोषण", "बाल तस्करी", "जबरन मजदूरी",
                "दलाल", "वेश्यालय", "अपहरण",
            ],
            "weight": 0.35,
        },
        "narcotics": {
            "keywords": [
                "narcotics", "drug trafficking", "drug cartel", "mdma", "ecstasy",
                "cocaine", "heroin", "methamphetamine", "meth", "crystal meth",
                "fentanyl", "opium", "morphine", "codeine", "hydrocodone", "oxycodone",
                "fentanyl patch", "fentanyl citrate", "carfentanil", "lsd", "acid",
                "shrooms", "psilocybin", "marijuana", "cannabis", "weed", "hashish",
                "charas", "ganja", "bhang", "opium poppy", "coca leaf", "cocaine paste",
                "drug lab", "pill press", "counterfeit pills", "research chemicals",
                "bath salts", "synthetic weed", "k2", "spice", "rc benzos",
                "drug cartel", "narco trafficking", "narco terror", "golden crescent",
                "golden triangle", "drug mule", "pill trafficking",
                # Chinese keywords for Golden Triangle / fentanyl
                "毒品", "海洛因", "可卡因", "冰毒", "芬太尼", "鸦片",
                "摇头丸", "大麻", "化学药品", "制毒", "贩毒",
                "金三角", "毒品走私", "麻醉药品", "精神药物",
                # Urdu keywords for Afghan heroin
                "منشیات", "ہیروئن", "کوکین", "افیم", "چرس", "گاجا",
                "نشہ آور ادویات", "منشیات فروش", "منشیات اسمگلنگ",
                "سنہری کریسنٹ", "افغان ہیروئن",
                # Persian/Farsi keywords
                "مواد مخدر", "هروئین", "کوکائین", "تریاک", "حشیش",
                "قاچاق مواد مخدر", "کارتل مواد مخدر", "شیشه",
            ],
            "weight": 0.3,
        },
        "cyber_espionage": {
            "keywords": [
                "cyber espionage", "espionage", "state sponsored", "state actor",
                "apt attack", "advanced persistent threat", "cyber warfare",
                "cyber weapon", "cyber operation", "information warfare",
                "influence operation", "disinformation", "propaganda",
                "election interference", "cyber sabotage", "critical infrastructure",
                "industrial espionage", "trade secret theft", "ip theft",
                "intellectual property theft", "economic espionage",
                "cyber command", "signals intelligence", "sigint",
                "cyber attack", "cyber weapon", "stuxnet", "duqu", "flame",
                "hacking team", "nsa", "gchq", "fsb", "gru", "mss", "ntro",
                # Chinese (Mandarin) keywords for China-linked cyber operations
                "网络间谍", "网络攻击", "网络战", "网络武器", "网络行动",
                "网络入侵", "网络窃密", "网络渗透", "网络侦查", "网络破坏",
                "信息战", "电子战", "网络军", "中国黑客", "国家支持",
                "网络钓鱼", "木马", "后门", "漏洞", "零日漏洞",
                "供应链攻击", "数据窃取", "间谍软件", "监视", "网络犯罪",
                # Russian keywords for state-sponsored operations
                "кибершпионаж", "кибератака", "кибервойна", "кибероружие",
                "шпионаж", "господдержка", "государственный хакер", "фсб", "гру",
                "разведка", "информационная война", "вмешательство",
                # Arabic keywords
                "تجسس إلكتروني", "هجوم إلكتروني", "حرب إلكترونية", "سلاح إلكتروني",
                "جاسوسية", "دعم الدولة", "اختراق", "تسريب", "تجسس",
            ],
            "weight": 0.35,
        },
    }

    def __init__(self):
        self._loaded = True

    async def classify(self, text: str, title: str = "") -> Dict:
        """Classify text into threat categories with confidence scores."""
        if not text and not title:
            return {
                "primary": "unknown",
                "secondary": [],
                "confidence": 0.0,
                "all_scores": {},
            }

        combined = f"{title} {text}".lower()
        word_count = len(combined.split())
        if word_count == 0:
            word_count = 1

        scores = {}
        for category, config in self.CATEGORY_KEYWORDS.items():
            category_score = 0.0
            matches = 0
            total_weight = 0.0

            for kw in config["keywords"]:
                pattern = r"\b" + re.escape(kw) + r"\b"
                found = len(re.findall(pattern, combined, re.IGNORECASE))
                if found > 0:
                    matches += found
                    total_weight += config["weight"]

            if matches > 0:
                # Score based on keyword density and weight
                density = matches / max(word_count, 1)
                category_score = min(1.0, density * 50 + total_weight)
                # Boost for title matches
                if title and any(kw in title.lower() for kw in config["keywords"]):
                    category_score = min(1.0, category_score * 1.5)

            scores[category] = round(category_score, 4)

        # Determine primary and secondary categories
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = "unknown"
        secondary = []
        confidence = 0.0

        if sorted_categories and sorted_categories[0][1] > 0.05:
            primary = sorted_categories[0][0]
            confidence = sorted_categories[0][1]
            for cat, score in sorted_categories[1:]:
                if score > 0.1:
                    secondary.append(cat)
                if len(secondary) >= 3:
                    break

        # Normalize confidence
        confidence = min(1.0, confidence)

        return {
            "primary": primary,
            "secondary": secondary,
            "confidence": round(confidence, 4),
            "all_scores": scores,
        }

    async def get_categories(self) -> List[str]:
        """Return list of all supported categories."""
        return self.CATEGORIES.copy()


# Singleton
_classifier: Optional[ThreatClassifier] = None


async def get_classifier() -> ThreatClassifier:
    """Get or create the singleton classifier."""
    global _classifier
    if _classifier is None:
        _classifier = ThreatClassifier()
    return _classifier
