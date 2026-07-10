"""Named Entity Recognition pipeline — extracts persons, orgs, PII, financial data from text."""

import logging
import re
from typing import Dict, List, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extracts named entities, PII, and financial data from text content."""

    def __init__(self):
        self._nlp = None
        self._model_loaded = False

        # Compiled regex patterns
        self.btc_pattern = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        self.eth_pattern = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
        self.xmr_pattern = re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        self.phone_pattern = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}")
        self.ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        self.ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        self.credit_card_pattern = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
        self.aadhaar_pattern = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
        self.pan_pattern = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
        self.url_pattern = re.compile(r"https?://[^\s<>\"']+|onion:[^\s<>\"']+")

        # Indian-specific PII patterns
        self.voter_id_pattern = re.compile(r"\b[A-Z]{3}\d{7}\b")  # E.g. ABC1234567
        self.dl_pattern = re.compile(r"\b(?:[A-Z]{2}\d{2}|[A-Z]{2}\d{13})\b")  # DL format
        self.upi_pattern = re.compile(r"\b[\w.-]+@[a-zA-Z]{3,}\b")  # UPI IDs like xyz@paytm, abc@upi
        self.gst_pattern = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}\b")  # GSTIN
        self.ifsc_pattern = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")  # IFSC code
        self.account_pattern = re.compile(r"\b\d{9,18}\b")  # Bank account numbers (9-18 digits)
        self.passport_pattern = re.compile(r"\b[A-Z][0-9]{7}\b")  # Indian passport
        self.vehicle_pattern = re.compile(r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,2}\s?\d{1,4}\b")  # Indian vehicle reg
        # Credit card BIN (first 6 digits)
        self.cc_bin_pattern = re.compile(r"\b(4\d{5}|5[1-5]\d{4}|3[47]\d{4}|6\d{5})\b")

        # International PII patterns
        # Chinese ID (18 digits)
        self.chinese_id_pattern = re.compile(r"\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b")
        # Chinese passport
        self.chinese_passport_pattern = re.compile(r"\b[EeGg]\d{8}\b")
        # Chinese mobile (1xx-xxxx-xxxx)
        self.chinese_phone_pattern = re.compile(r"\b1[3-9]\d{9}\b")
        # Russian passport (series + number)
        self.russian_passport_pattern = re.compile(r"\b\d{2}\s?\d{2}\s?\d{6}\b")
        # Russian internal passport
        self.russian_internal_pattern = re.compile(r"\b\d{4}\s?\d{6}\b")
        # Pakistani ID card (13 digits with dashes)
        self.pakistan_id_pattern = re.compile(r"\b[1-9]\d{4}-\d{7}-\d{1}\b")
        # Pakistani passport
        self.pakistan_passport_pattern = re.compile(r"\b[A-Z]{2}\d{7}\b")
        # Bangladeshi ID (10-17 digits)
        self.bangladesh_id_pattern = re.compile(r"\b\d{10,17}\b")
        # IBAN (international bank account)
        self.iban_pattern = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b")
        # SWIFT/BIC codes
        self.swift_pattern = re.compile(r"\b[A-Z]{6}[A-Z0-9]{2,5}\b")
        # International passport numbers (generic format)
        self.intl_passport_pattern = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")

        # ── Dark Web Specific Entities ───────────────────────────────────────
        # .onion addresses (Tor hidden services)
        self.onion_pattern = re.compile(r"\b[a-z2-7]{16,56}\.onion\b")
        # .i2p addresses
        self.i2p_pattern = re.compile(r"\b[a-z0-9-]+\.i2p\b")
        # Darknet marketplace listings (common formats)
        self.marketplace_listing_pattern = re.compile(r"(?i)(?:listing|item|product|ad)\s*[#:]?\s*[A-Z0-9]{5,12}")
        # Bitcoin mixers / tumblers
        self.mixer_pattern = re.compile(r"(?i)(?:bitcoin|btc|crypto)\s*(?:mixer|tumbler|cleaner|washer|fog)")
        # Carding shops
        self.carding_shop_pattern = re.compile(r"(?i)(?:dumpshop|cardingshop|dumps\s+shop|cc\s+shop|card\s+shop)")
        # Telegram/WhatsApp/Discord invite patterns
        self.messenger_pattern = re.compile(r"(?:t\.me/|telegram\.me/|discord\.gg/|whatsapp\.com/channel/|invite\.gg/)[a-zA-Z0-9_]+")
        # Protonmail / Tutanota (encrypted email domains)
        self.encrypted_email_pattern = re.compile(r"\b[a-zA-Z0-9._%+-]+@(?:protonmail\.com|proton\.me|tutanota\.com|tuta\.io|ctemplar\.com|guerrillamail\.com)\b")
        # Session / Signal / Wickr contact info
        self.messenger_id_pattern = re.compile(r"(?i)(?:session|signal|wickr|matrix|tox)\s*[id:]*\s*[a-zA-Z0-9]{10,60}")
        # Crypto wallet setup patterns (seed phrases)
        self.seed_phrase_pattern = re.compile(r"\b(?:seed\s*phrase|mnemonic|recovery\s*phrase|wallet\s*seed)\s*:?\s*[a-z\s]{20,100}\b")

    async def load_model(self):
        """Load spaCy model (lazy-loaded)."""
        if not self._model_loaded:
            try:
                import spacy
                settings = get_settings()
                model_name = settings.SPACY_MODEL_EN or "en_core_web_sm"
                self._nlp = spacy.load(model_name)
                self._model_loaded = True
                logger.info("spaCy NER model loaded: %s", model_name)
            except Exception as e:
                logger.warning("Failed to load spaCy model: %s. Using regex-only NER.", e)
                self._model_loaded = True  # Don't retry

    async def extract_all(self, text: str) -> Dict[str, List[str]]:
        """Extract all entities from text using spaCy NER and regex."""
        await self.load_model()

        entities = {
            "persons": [],
            "organizations": [],
            "gpe": [],  # Geopolitical entities
            "products": [],
            "emails": [],
            "btc_addresses": [],
            "eth_addresses": [],
            "xmr_addresses": [],
            "phone_numbers": [],
            "ip_addresses": [],
            "urls": [],
            "credit_cards": [],
            "ssn": [],
            "aadhaar": [],
            "pan": [],
            "voter_id": [],
            "driving_license": [],
            "upi_ids": [],
            "gst_numbers": [],
            "ifsc_codes": [],
            "bank_accounts": [],
            "passport": [],
            "vehicle_registration": [],
            "credit_card_bins": [],
            "money": [],
            "dates": [],
            # International PII
            "chinese_id": [],
            "chinese_passport": [],
            "chinese_phone": [],
            "russian_passport": [],
            "pakistan_id": [],
            "pakistan_passport": [],
            "bangladesh_id": [],
            "iban": [],
            "swift": [],
            "international_passport": [],
            # Dark web specific entities
            "onion_addresses": [],
            "i2p_addresses": [],
            "marketplace_listings": [],
            "crypto_mixers": [],
            "carding_shops": [],
            "messenger_invites": [],
            "encrypted_emails": [],
            "messenger_ids": [],
            "seed_phrases": [],
        }

        # Regex-based extraction (always available)
        entities["emails"] = list(set(self.email_pattern.findall(text)))
        entities["btc_addresses"] = list(set(self.btc_pattern.findall(text)))
        entities["eth_addresses"] = list(set(self.eth_pattern.findall(text)))
        entities["xmr_addresses"] = list(set(self.xmr_pattern.findall(text)))
        entities["phone_numbers"] = list(set(self.phone_pattern.findall(text)))
        entities["ip_addresses"] = list(set(self.ip_pattern.findall(text)))
        entities["urls"] = list(set(self.url_pattern.findall(text)))
        entities["credit_cards"] = list(set(self.credit_card_pattern.findall(text)))
        entities["ssn"] = list(set(self.ssn_pattern.findall(text)))
        entities["aadhaar"] = list(set(self.aadhaar_pattern.findall(text)))
        entities["pan"] = list(set(self.pan_pattern.findall(text)))
        # Indian-specific PII regex
        entities["voter_id"] = list(set(self.voter_id_pattern.findall(text)))
        entities["driving_license"] = list(set(self.dl_pattern.findall(text)))
        entities["upi_ids"] = list(set(self.upi_pattern.findall(text)))
        entities["gst_numbers"] = list(set(self.gst_pattern.findall(text)))
        entities["ifsc_codes"] = list(set(self.ifsc_pattern.findall(text)))
        entities["passport"] = list(set(self.passport_pattern.findall(text)))
        entities["vehicle_registration"] = list(set(self.vehicle_pattern.findall(text)))
        entities["credit_card_bins"] = list(set(self.cc_bin_pattern.findall(text)))
        # Bank account numbers (filtered to avoid matching short numbers)
        account_matches = [m.group() for m in self.account_pattern.finditer(text) if len(m.group()) >= 9]
        entities["bank_accounts"] = list(set(account_matches))

        # International PII regex extraction
        entities["chinese_id"] = list(set(self.chinese_id_pattern.findall(text)))
        entities["chinese_passport"] = list(set(self.chinese_passport_pattern.findall(text)))
        entities["chinese_phone"] = list(set(self.chinese_phone_pattern.findall(text)))
        entities["russian_passport"] = list(set(self.russian_passport_pattern.findall(text)))
        entities["pakistan_id"] = list(set(self.pakistan_id_pattern.findall(text)))
        entities["pakistan_passport"] = list(set(self.pakistan_passport_pattern.findall(text)))
        entities["bangladesh_id"] = list(set(self.bangladesh_id_pattern.findall(text)))
        entities["iban"] = list(set(self.iban_pattern.findall(text)))
        entities["swift"] = list(set(self.swift_pattern.findall(text)))
        entities["international_passport"] = list(set(self.intl_passport_pattern.findall(text)))

        # Dark web specific entities
        entities["onion_addresses"] = list(set(self.onion_pattern.findall(text)))
        entities["i2p_addresses"] = list(set(self.i2p_pattern.findall(text)))
        entities["marketplace_listings"] = list(set(self.marketplace_listing_pattern.findall(text)))
        entities["crypto_mixers"] = list(set(self.mixer_pattern.findall(text)))
        entities["carding_shops"] = list(set(self.carding_shop_pattern.findall(text)))
        entities["messenger_invites"] = list(set(self.messenger_pattern.findall(text)))
        entities["encrypted_emails"] = list(set(self.encrypted_email_pattern.findall(text)))
        entities["messenger_ids"] = list(set(self.messenger_id_pattern.findall(text)))
        entities["seed_phrases"] = list(set(self.seed_phrase_pattern.findall(text)))

        # spaCy NER extraction
        if self._nlp and text.strip():
            try:
                # Process in chunks to avoid memory issues
                chunk_size = 50000
                if len(text) > chunk_size:
                    text = text[:chunk_size]

                doc = self._nlp(text)

                for ent in doc.ents:
                    label = ent.label_
                    text_val = ent.text.strip()

                    if label == "PERSON":
                        if text_val not in entities["persons"]:
                            entities["persons"].append(text_val)
                    elif label == "ORG":
                        if text_val not in entities["organizations"]:
                            entities["organizations"].append(text_val)
                    elif label in ("GPE", "LOC"):
                        if text_val not in entities["gpe"]:
                            entities["gpe"].append(text_val)
                    elif label == "PRODUCT":
                        if text_val not in entities["products"]:
                            entities["products"].append(text_val)
                    elif label == "MONEY":
                        if text_val not in entities["money"]:
                            entities["money"].append(text_val)
                    elif label == "DATE":
                        if text_val not in entities["dates"]:
                            entities["dates"].append(text_val)

            except Exception as e:
                logger.warning("spaCy NER failed: %s", e)

        # Remove empty lists
        return {k: v for k, v in entities.items() if v}

    async def extract_pii(self, text: str) -> Dict[str, List[str]]:
        """Extract only PII-related entities."""
        all_entities = await self.extract_all(text)
        pii_fields = ["emails", "phone_numbers", "ssn", "credit_cards", "aadhaar", "pan",
                        "voter_id", "driving_license", "upi_ids", "gst_numbers",
                        "ifsc_codes", "bank_accounts", "passport", "vehicle_registration",
                        "credit_card_bins", "ip_addresses"]
        return {k: all_entities.get(k, []) for k in pii_fields if all_entities.get(k)}

    async def extract_financial(self, text: str) -> Dict[str, List[str]]:
        """Extract financial entities (crypto addresses, credit cards, money amounts)."""
        all_entities = await self.extract_all(text)
        financial_fields = ["btc_addresses", "eth_addresses", "xmr_addresses", "credit_cards", "money"]
        return {k: all_entities.get(k, []) for k in financial_fields if all_entities.get(k)}


# Singleton
_entity_extractor: Optional[EntityExtractor] = None


async def get_entity_extractor() -> EntityExtractor:
    """Get or create the singleton entity extractor."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
        await _entity_extractor.load_model()
    return _entity_extractor
