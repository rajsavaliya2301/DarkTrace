"""Content parsers for marketplaces, forums, paste sites, and generic HTML."""

import json
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ParsedContent:
    """Result of parsing raw HTML/content."""

    def __init__(
        self,
        url: str,
        source_type: str,
        site_name: str,
        document_type: str,
        title: str = "",
        author: str = "",
        author_profile_url: str = "",
        published_date: Optional[str] = None,
        content_text: str = "",
        language: str = "en",
        entities: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ):
        self.url = url
        self.source_type = source_type
        self.site_name = site_name
        self.document_type = document_type
        self.title = title
        self.author = author
        self.author_profile_url = author_profile_url
        self.published_date = published_date
        self.content_text = content_text
        self.language = language
        self.entities = entities or {
            "emails": [],
            "btc_addresses": [],
            "eth_addresses": [],
            "xmr_addresses": [],
            "urls": [],
            "phone_numbers": [],
            "ip_addresses": [],
        }
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "source_type": self.source_type,
            "site_name": self.site_name,
            "document_type": self.document_type,
            "title": self.title,
            "author": self.author,
            "author_profile_url": self.author_profile_url,
            "published_date": self.published_date,
            "content_text": self.content_text,
            "language": self.language,
            "entities": self.entities,
            "metadata": self.metadata,
        }


class ContentParser:
    """Main content parser with site-specific and generic fallback parsing."""

    def __init__(self):
        # BTC address pattern
        self.btc_pattern = re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b")
        # ETH address pattern
        self.eth_pattern = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
        # XMR address pattern
        self.xmr_pattern = re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b")
        # Email pattern
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
        # Phone pattern (international format)
        self.phone_pattern = re.compile(r"\+\d{1,3}[-\s]?\d{1,14}(?:[-\s]?\d{1,13})?")
        # IP pattern
        self.ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
        # URL pattern
        self.url_pattern = re.compile(r"https?://[^\s<>\"']+|onion:[^\s<>\"']+")

    def parse(self, url: str, source_type: str, site_name: str, raw_html: str, content_type: str) -> ParsedContent:
        """Parse raw content. Routes to appropriate parser based on site type."""
        # Detect document type
        document_type = self._classify_document(raw_html, url)

        # Try site-specific parser
        parser_func = self._get_site_parser(site_name, document_type)
        if parser_func:
            try:
                return parser_func(url, source_type, site_name, raw_html)
            except Exception as e:
                logger.warning("Site-specific parser failed for %s: %s. Using fallback.", site_name, e)

        # Generic fallback parser
        return self._parse_generic(url, source_type, site_name, raw_html, document_type)

    def _classify_document(self, raw_html: str, url: str) -> str:
        """Classify the document type from content and URL."""
        url_lower = url.lower()

        if any(kw in url_lower for kw in ["/listing", "/product", "/item", "/shop"]):
            return "marketplace_listing"
        if any(kw in url_lower for kw in ["/forum", "/thread", "/topic", "/post", "/board"]):
            return "forum_post"
        if any(kw in url_lower for kw in ["/paste", "/doc", "/text"]):
            return "paste"
        if any(kw in url_lower for kw in ["/login", "/register", "/auth"]):
            return "auth_page"
        if any(kw in url_lower for kw in ["/search", "/browse", "/category"]):
            return "listing_page"

        # Check content for clues
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ", strip=True).lower()

        if any(kw in text for kw in ["listing", "price", "buy now", "add to cart", "bitcoin", "escrow"]):
            return "marketplace_listing"
        if any(kw in text for kw in ["reply", "quote", "posted by", "member", "forum"]):
            return "forum_post"
        if any(kw in text for kw in ["paste", "raw text", "plain text"]):
            return "paste"

        return "unknown"

    def _get_site_parser(self, site_name: str, document_type: str):
        """Get the appropriate parser function for a known site."""
        parsers = {
            "example_market": {
                "marketplace_listing": self._parse_marketplace_listing,
            },
            "dark_hub": {
                "forum_post": self._parse_forum_post,
            },
        }
        site_parsers = parsers.get(site_name.lower().replace(" ", "_"))
        if site_parsers:
            return site_parsers.get(document_type)
        return None

    def _parse_generic(self, url: str, source_type: str, site_name: str, raw_html: str, document_type: str) -> ParsedContent:
        """Generic fallback parser using BeautifulSoup."""
        soup = BeautifulSoup(raw_html, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Try meta title
        if not title:
            meta_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find("meta", attrs={"name": "title"})
            if meta_title:
                title = meta_title.get("content", "")

        # Extract main content
        content_text = ""
        article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|main|body|post"))
        if article:
            content_text = article.get_text(separator=" ", strip=True)
        else:
            content_text = soup.get_text(separator=" ", strip=True)

        # Truncate very long content
        if len(content_text) > 50000:
            content_text = content_text[:50000]

        # Extract author
        author = ""
        author_patterns = [
            soup.find("meta", attrs={"name": "author"}),
            soup.find("span", class_=re.compile(r"author|username|poster")),
            soup.find("a", class_=re.compile(r"author|username|poster")),
        ]
        for el in author_patterns:
            if el:
                author = el.get("content", "") if el.name == "meta" else el.get_text(strip=True)
                if author:
                    break

        # Extract date
        published_date = ""
        date_patterns = [
            soup.find("meta", attrs={"property": "article:published_time"}),
            soup.find("meta", attrs={"name": "date"}),
            soup.find("time"),
            soup.find("span", class_=re.compile(r"date|time|posted")),
        ]
        for el in date_patterns:
            if el:
                published_date = el.get("content", "") or el.get("datetime", "") or el.get_text(strip=True)
                if published_date:
                    break

        # Pre-extract entities
        entities = self._extract_entities(content_text)

        return ParsedContent(
            url=url,
            source_type=source_type,
            site_name=site_name,
            document_type=document_type,
            title=title,
            author=author,
            content_text=content_text,
            published_date=published_date,
            entities=entities,
        )

    def _parse_marketplace_listing(self, url: str, source_type: str, site_name: str, raw_html: str) -> ParsedContent:
        """Parse a marketplace listing page."""
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        title = ""
        title_tag = soup.find("h1") or soup.find("h2")
        if title_tag:
            title = title_tag.get_text(strip=True)

        author = ""
        author_el = soup.find("span", class_=re.compile(r"vendor|seller|author|username"))
        if author_el:
            author = author_el.get_text(strip=True)

        content_text = soup.get_text(separator=" ", strip=True)

        # Extract price
        price = ""
        price_el = soup.find(string=re.compile(r"\$\d+\.?\d*|USD|BTC|€"))
        if price_el:
            price = str(price_el).strip()

        # Extract category/product info
        category = ""
        cat_el = soup.find("span", class_=re.compile(r"category|tag"))
        if cat_el:
            category = cat_el.get_text(strip=True)

        entities = self._extract_entities(content_text)

        result = self._parse_generic(url, source_type, site_name, raw_html, "marketplace_listing")
        result.metadata["price"] = price
        result.metadata["category"] = category
        return result

    def _parse_forum_post(self, url: str, source_type: str, site_name: str, raw_html: str) -> ParsedContent:
        """Parse a forum post page."""
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()

        title = ""
        title_tag = soup.find("h1") or soup.find("h2")
        if title_tag:
            title = title_tag.get_text(strip=True)

        author = ""
        author_el = soup.find("span", class_=re.compile(r"author|username|poster")) or soup.find("a", class_=re.compile(r"author"))
        if author_el:
            author = author_el.get_text(strip=True)

        content_text = soup.get_text(separator=" ", strip=True)
        entities = self._extract_entities(content_text)

        return ParsedContent(
            url=url,
            source_type=source_type,
            site_name=site_name,
            document_type="forum_post",
            title=title,
            author=author,
            content_text=content_text,
            entities=entities,
        )

    def _extract_entities(self, text: str) -> dict:
        """Extract entities (BTC, ETH, XMR, emails, phones, IPs, URLs) from text."""
        return {
            "emails": list(set(self.email_pattern.findall(text))),
            "btc_addresses": list(set(self.btc_pattern.findall(text))),
            "eth_addresses": list(set(self.eth_pattern.findall(text))),
            "xmr_addresses": list(set(self.xmr_pattern.findall(text))),
            "urls": list(set(self.url_pattern.findall(text))),
            "phone_numbers": list(set(self.phone_pattern.findall(text))),
            "ip_addresses": list(set(self.ip_pattern.findall(text))),
        }
