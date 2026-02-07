"""
Text extraction utility for Vanush.
Tries multiple methods to extract article text from a URL:
  1. Direct HTTP fetch + BeautifulSoup (fast, works on most sites)
  2. PDF download + pypdf (for PDF links)
  3. Returns None if all methods fail

All agents should call extract_text(url) instead of relying on
Firecrawl to scrape inside the LLM prompt.
"""

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import tempfile
import os
import re
from typing import Optional


# Common headers to avoid bot detection
HEADERS = {
    "User-Agent": (
        "Vanush/1.0 (Academic Paper Analyzer; "
        "https://github.com/vanush) "
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Maximum text length to send to LLM (roughly ~60k tokens)
MAX_TEXT_LENGTH = 200_000


def is_pdf_url(url: str) -> bool:
    """Check if a URL points to a PDF file."""
    url_lower = url.lower()
    # Direct .pdf extension
    if url_lower.endswith(".pdf"):
        return True
    # Common academic PDF patterns
    if "/pdf/" in url_lower:
        return True
    return False


def extract_from_pdf(url: str) -> Optional[str]:
    """
    Download a PDF from a URL and extract its text.
    Uses pypdf to read the PDF content.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        response.raise_for_status()

        # Verify we actually got a PDF
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type and not url.lower().endswith(".pdf"):
            # Check magic bytes
            if not response.content[:5] == b"%PDF-":
                return None

        # Write to temp file and extract
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name

        try:
            reader = PdfReader(tmp_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            text = "\n\n".join(text_parts)
            if len(text.strip()) < 100:
                return None  # PDF was likely scanned/image-based
            return text[:MAX_TEXT_LENGTH]
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        print(f"[text_extractor] PDF extraction failed: {e}")
        return None


def extract_from_html(url: str) -> Optional[str]:
    """
    Fetch a webpage via HTTP and extract article text using BeautifulSoup.
    Strips navigation, scripts, ads, and other non-content elements.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        response.raise_for_status()

        print(f"[text_extractor] HTTP {response.status_code} from {url} ({len(response.text)} bytes)")

        # Check we got HTML
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type and "text" not in content_type:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Step 1: Find the main content container FIRST (before removing anything)
        article_text = None
        content_container = None

        # Try specific content selectors in priority order
        content_selectors = [
            "article",
            "#mw-content-text .mw-parser-output",  # Wikipedia
            "#mw-content-text",                      # Wikipedia fallback
            "[class*='article-body']",
            "[class*='article-content']",
            "[class*='post-content']",
            "[class*='entry-content']",
            "[class*='story-body']",
            "[class*='content-body']",
            "[class*='prose']",
            ".caas-body",
            "#article-body",
            "main",
            "[role='main']",
        ]

        for selector in content_selectors:
            found = soup.select_one(selector)
            if found and len(found.get_text(strip=True)) > 200:
                content_container = found
                print(f"[text_extractor] Found content via selector: {selector}")
                break

        # Fallback to body
        if not content_container:
            content_container = soup.find("body")
            if content_container:
                print(f"[text_extractor] Falling back to <body>")

        if not content_container:
            print(f"[text_extractor] No content container found")
            return None

        # Step 2: NOW strip non-content elements from WITHIN the container
        for tag in content_container.find_all([
            "script", "style", "nav", "footer", "header",
            "aside", "form", "iframe", "noscript",
            "button", "input", "select", "textarea",
            "sup",  # remove footnote markers for cleaner text
        ]):
            tag.decompose()

        # Remove common junk classes/IDs within the container
        for selector in [
            "[class*='sidebar']", "[class*='footer']",
            "[class*='header']", "[class*='menu']", "[class*='cookie']",
            "[class*='banner']", "[class*='popup']", "[class*='modal']",
            "[class*='social']", "[class*='share']", "[class*='comment']",
            "[class*='navbox']", "[class*='navbar']",
            "[class*='infobox']", "[class*='toc']",
            "[class*='mw-editsection']", "[class*='reference']",
            "[class*='reflist']", "[class*='noprint']",
            "[id*='sidebar']", "[id*='footer']",
            "[id*='header']", "[id*='menu']", "[id*='cookie']",
        ]:
            for tag in content_container.select(selector):
                tag.decompose()

        # Step 3: Extract text
        article_text = content_container.get_text(separator="\n", strip=True)

        if not article_text:
            print(f"[text_extractor] Content container was empty after cleanup")
            return None

        # Clean up the text
        text = clean_text(article_text)
        print(f"[text_extractor] Extracted {len(text)} chars after cleanup")

        if len(text.strip()) < 100:
            print(f"[text_extractor] Too little content ({len(text.strip())} chars)")
            return None  # Too little content, probably blocked

        return text[:MAX_TEXT_LENGTH]

    except requests.exceptions.HTTPError as e:
        print(f"[text_extractor] HTML extraction failed: HTTP {e.response.status_code} from {url}")
        return None
    except Exception as e:
        print(f"[text_extractor] HTML extraction failed: {e}")
        return None


def extract_from_arxiv(url: str) -> Optional[str]:
    """
    Special handler for arXiv URLs.
    Converts abstract page URLs to PDF URLs and extracts text.
    e.g. https://arxiv.org/abs/2301.00001 -> https://arxiv.org/pdf/2301.00001
    """
    # Match arXiv abstract URLs
    arxiv_match = re.match(r"https?://arxiv\.org/abs/(.+?)/?$", url)
    if arxiv_match:
        paper_id = arxiv_match.group(1)
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        print(f"[text_extractor] Converting arXiv URL to PDF: {pdf_url}")
        return extract_from_pdf(pdf_url)
    return None


def clean_text(text: str) -> str:
    """Clean extracted text by removing excess whitespace and artifacts."""
    # Collapse multiple newlines into double newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)
    # Remove lines that are just whitespace
    lines = [line for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)
    return text.strip()


def extract_text(url: str) -> Optional[str]:
    """
    Main extraction function. Tries multiple methods in order:
    1. arXiv special handler (if arXiv URL)
    2. PDF extraction (if URL looks like a PDF)
    3. HTML extraction via BeautifulSoup
    4. PDF extraction as last resort (some URLs serve PDF without .pdf extension)

    Returns extracted text or None if all methods fail.
    """
    print(f"[text_extractor] Extracting text from: {url}")

    # 1. arXiv special case
    if "arxiv.org" in url:
        text = extract_from_arxiv(url)
        if text:
            print(f"[text_extractor] ✅ arXiv PDF extraction succeeded ({len(text)} chars)")
            return text

    # 2. Direct PDF link
    if is_pdf_url(url):
        text = extract_from_pdf(url)
        if text:
            print(f"[text_extractor] ✅ PDF extraction succeeded ({len(text)} chars)")
            return text

    # 3. HTML extraction (most common case)
    text = extract_from_html(url)
    if text:
        print(f"[text_extractor] ✅ HTML extraction succeeded ({len(text)} chars)")
        return text

    # 4. Last resort: try as PDF anyway (some servers don't use .pdf extension)
    text = extract_from_pdf(url)
    if text:
        print(f"[text_extractor] ✅ Fallback PDF extraction succeeded ({len(text)} chars)")
        return text

    print(f"[text_extractor] ❌ All extraction methods failed for: {url}")
    return None


# Async wrapper for use in async agent code
async def async_extract_text(url: str) -> Optional[str]:
    """
    Async wrapper around extract_text.
    Runs the synchronous extraction in a thread pool to avoid blocking.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_text, url)