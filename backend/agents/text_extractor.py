import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import tempfile
import os
import re
from typing import Optional
from urllib.parse import urlparse, urljoin


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
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

# Maximum text length to send to LLM (roughly ~60k tokens)
MAX_TEXT_LENGTH = 200_000
MIN_TEXT_LENGTH_GENERAL = 250
MIN_TEXT_LENGTH_SCHOLARLY = 1200

SCHOLARLY_DOMAINS = [
    "link.springer.com",
    "springer.com",
    "onlinelibrary.wiley.com",
    "sciencedirect.com",
    "ieeexplore.ieee.org",
    "nature.com",
    "tandfonline.com",
    "sagepub.com",
]


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


def is_scholarly_url(url: str) -> bool:
    """Check if URL belongs to a scholarly publisher where abstracts are common."""
    host = urlparse(url).netloc.lower()
    return any(domain in host for domain in SCHOLARLY_DOMAINS)


def has_sufficient_text(url: str, text: str) -> bool:
    """Decide if extracted text is likely full content vs. just abstract/header."""
    min_len = MIN_TEXT_LENGTH_SCHOLARLY if is_scholarly_url(url) else MIN_TEXT_LENGTH_GENERAL
    text_len = len(text.strip())
    if text_len < min_len:
        print(
            f"[text_extractor] Text too short for {urlparse(url).netloc} "
            f"({text_len} < {min_len}), trying fallback methods"
        )
        return False
    return True


def extract_from_pdf(url: str) -> Optional[str]:
    """
    Download a PDF from a URL and extract its text.
    Uses pypdf to read the PDF content.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        response.raise_for_status()
        return extract_pdf_bytes(response.content, url=url)
    except Exception as e:
        print(f"[text_extractor] PDF extraction failed: {e}")
        return None


def extract_pdf_bytes(pdf_bytes: bytes, url: str = "") -> Optional[str]:
    """Extract text from raw PDF bytes."""
    try:
        # Verify we actually got a PDF
        if not pdf_bytes[:5] == b"%PDF-":
            return None

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
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
        suffix = f" ({url})" if url else ""
        print(f"[text_extractor] PDF byte extraction failed{suffix}: {e}")
        return None


def extract_from_local_pdf(path: str) -> Optional[str]:
    """Extract text directly from a local PDF path."""
    try:
        with open(path, "rb") as f:
            return extract_pdf_bytes(f.read(), url=path)
    except Exception as e:
        print(f"[text_extractor] Local PDF extraction failed ({path}): {e}")
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


def build_fallback_urls(url: str) -> list[str]:
    """
    Build likely alternate URLs for sources that block direct access to one path.
    Example: Wiley often blocks /doi/epdf/ but allows /doi/pdf/ or /doi/pdfdirect/.
    """
    variants: list[str] = []

    def add(candidate: str) -> None:
        if candidate and candidate != url and candidate not in variants:
            variants.append(candidate)

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "onlinelibrary.wiley.com" in host:
        add(url.replace("/doi/epdf/", "/doi/pdf/"))
        add(url.replace("/doi/epdf/", "/doi/pdfdirect/"))
        add(url.replace("/doi/full/", "/doi/pdf/"))
        add(url.replace("/doi/full/", "/doi/pdfdirect/"))
        add(url.replace("/doi/abs/", "/doi/pdf/"))
        add(url.replace("/doi/abs/", "/doi/pdfdirect/"))

    # Generic publisher fallback where /epdf/ is blocked.
    add(url.replace("/epdf/", "/pdf/"))

    # Some providers only return file content with explicit download flag.
    for candidate in list(variants):
        joiner = "&" if "?" in candidate else "?"
        add(f"{candidate}{joiner}download=true")

    return variants


def extract_doi(url: str) -> Optional[str]:
    """Extract DOI from common publisher URL paths."""
    doi_match = re.search(r"/doi/(?:epdf|pdfdirect|pdf|full|abs)?/?(10\.\d{4,9}/[^?#]+)", url)
    if doi_match:
        return doi_match.group(1).strip("/")
    doi_match = re.search(r"/(?:article|chapter)/(10\.\d{4,9}/[^?#]+)", url)
    if doi_match:
        return doi_match.group(1).strip("/")
    return None


def discover_pdf_links_from_html(html: str, base_url: str) -> list[str]:
    """Discover likely PDF links from an HTML page."""
    links: list[str] = []

    def add(link: str) -> None:
        absolute = urljoin(base_url, link)
        if absolute not in links:
            links.append(absolute)

    soup = BeautifulSoup(html, "html.parser")
    meta_pdf = soup.find("meta", attrs={"name": "citation_pdf_url"})
    if meta_pdf and meta_pdf.get("content"):
        add(meta_pdf["content"])

    for a in soup.find_all("a", href=True):
        href = a["href"]
        href_lower = href.lower()
        if (
            href_lower.endswith(".pdf")
            or "/doi/pdf/" in href_lower
            or "/doi/pdfdirect/" in href_lower
            or "pdf" in href_lower and "download" in href_lower
        ):
            add(href)

    return links


def extract_from_wiley(url: str) -> Optional[str]:
    """
    Wiley-specific flow:
    1. Load landing pages to establish session cookies.
    2. Discover PDF links in HTML metadata/anchors.
    3. Fetch PDF using the same session and extract text.
    """
    parsed = urlparse(url)
    if "onlinelibrary.wiley.com" not in parsed.netloc.lower():
        return None

    doi = extract_doi(url)
    if not doi:
        return None

    session = requests.Session()
    candidates = [
        f"https://onlinelibrary.wiley.com/doi/{doi}",
        f"https://onlinelibrary.wiley.com/doi/full/{doi}",
        f"https://onlinelibrary.wiley.com/doi/abs/{doi}",
        f"https://onlinelibrary.wiley.com/doi/pdf/{doi}",
        f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
    ]

    for candidate in candidates:
        try:
            response = session.get(candidate, headers=HEADERS, timeout=30, allow_redirects=True)
            print(f"[text_extractor] Wiley session fetch: {response.status_code} {candidate}")
            if response.status_code >= 400:
                continue

            # Direct PDF response
            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" in content_type or response.content[:5] == b"%PDF-":
                text = extract_pdf_bytes(response.content, url=candidate)
                if text:
                    return text
                continue

            # HTML: try extracting readable text, then discover PDF links.
            if "html" in content_type or "text" in content_type:
                html_text = clean_text(BeautifulSoup(response.text, "html.parser").get_text("\n", strip=True))
                if len(html_text) > 800:
                    return html_text[:MAX_TEXT_LENGTH]

                for pdf_link in discover_pdf_links_from_html(response.text, response.url):
                    try:
                        pdf_headers = dict(HEADERS)
                        pdf_headers["Referer"] = response.url
                        pdf_response = session.get(
                            pdf_link,
                            headers=pdf_headers,
                            timeout=30,
                            allow_redirects=True,
                        )
                        if pdf_response.status_code >= 400:
                            continue
                        text = extract_pdf_bytes(pdf_response.content, url=pdf_link)
                        if text:
                            print(f"[text_extractor] Wiley discovered PDF URL succeeded: {pdf_link}")
                            return text
                    except Exception as pdf_err:
                        print(f"[text_extractor] Wiley PDF discovery fetch failed: {pdf_err}")
                        continue
        except Exception as e:
            print(f"[text_extractor] Wiley session fetch failed: {e}")
            continue

    return None


def extract_from_springer(url: str) -> Optional[str]:
    """
    Springer-specific flow:
    1. Resolve DOI from article/chapter URL.
    2. Try known Springer PDF endpoints.
    3. Fall back to HTML + discovered PDF links.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if "link.springer.com" not in host:
        return None

    doi = extract_doi(url)
    if not doi:
        return None

    session = requests.Session()
    candidates = [
        f"https://link.springer.com/content/pdf/{doi}.pdf",
        f"https://link.springer.com/content/pdf/{doi}.pdf?download=1",
        f"https://link.springer.com/article/{doi}",
        f"https://link.springer.com/chapter/{doi}",
    ]

    for candidate in candidates:
        try:
            response = session.get(candidate, headers=HEADERS, timeout=30, allow_redirects=True)
            print(f"[text_extractor] Springer fetch: {response.status_code} {candidate}")
            if response.status_code >= 400:
                continue

            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" in content_type or response.content[:5] == b"%PDF-":
                text = extract_pdf_bytes(response.content, url=candidate)
                if text and has_sufficient_text(candidate, text):
                    return text
                continue

            if "html" in content_type or "text" in content_type:
                html_text = extract_from_html(response.url)
                if html_text and has_sufficient_text(response.url, html_text):
                    return html_text

                for pdf_link in discover_pdf_links_from_html(response.text, response.url):
                    try:
                        pdf_headers = dict(HEADERS)
                        pdf_headers["Referer"] = response.url
                        pdf_response = session.get(
                            pdf_link,
                            headers=pdf_headers,
                            timeout=30,
                            allow_redirects=True,
                        )
                        if pdf_response.status_code >= 400:
                            continue
                        text = extract_pdf_bytes(pdf_response.content, url=pdf_link)
                        if text and has_sufficient_text(pdf_link, text):
                            print(f"[text_extractor] Springer discovered PDF URL succeeded: {pdf_link}")
                            return text
                    except Exception as pdf_err:
                        print(f"[text_extractor] Springer PDF discovery fetch failed: {pdf_err}")
                        continue
        except Exception as e:
            print(f"[text_extractor] Springer fetch failed: {e}")
            continue

    return None


def extract_text_basic(url: str) -> Optional[str]:
    """
    Extraction strategy for a single URL. Tries methods in order:
    1. arXiv special handler (if arXiv URL)
    2. PDF extraction (if URL looks like a PDF)
    3. HTML extraction via BeautifulSoup
    4. PDF extraction as last resort (some URLs serve PDF without .pdf extension)
    """
    # 1. arXiv special case
    if "arxiv.org" in url:
        text = extract_from_arxiv(url)
        if text:
            print(f"[text_extractor] arXiv PDF extraction succeeded ({len(text)} chars)")
            return text

    # 2. Direct PDF link
    if is_pdf_url(url):
        text = extract_from_pdf(url)
        if text:
            print(f"[text_extractor] PDF extraction succeeded ({len(text)} chars)")
            return text

    # 3. HTML extraction (most common case)
    text = extract_from_html(url)
    if text:
        if has_sufficient_text(url, text):
            print(f"[text_extractor] HTML extraction succeeded ({len(text)} chars)")
            return text

    # 4. Last resort: try as PDF anyway (some servers don't use .pdf extension)
    text = extract_from_pdf(url)
    if text:
        if has_sufficient_text(url, text):
            print(f"[text_extractor] Fallback PDF extraction succeeded ({len(text)} chars)")
            return text

    print(f"[text_extractor] All extraction methods failed for: {url}")
    return None


def extract_text(url: str) -> Optional[str]:
    """
    Main extraction function with publisher URL fallbacks.
    Returns extracted text or None if all methods and URL variants fail.
    """
    print(f"[text_extractor] Extracting text from: {url}")

    if os.path.isfile(url) and url.lower().endswith(".pdf"):
        text = extract_from_local_pdf(url)
        if text:
            print(f"[text_extractor] Local PDF extraction succeeded ({len(text)} chars)")
            return text

    text = extract_text_basic(url)
    if text:
        return text

    text = extract_from_wiley(url)
    if text:
        print(f"[text_extractor] Wiley extraction succeeded ({len(text)} chars)")
        return text

    text = extract_from_springer(url)
    if text:
        print(f"[text_extractor] Springer extraction succeeded ({len(text)} chars)")
        return text

    fallback_urls = build_fallback_urls(url)
    for fallback_url in fallback_urls:
        print(f"[text_extractor] Trying fallback URL: {fallback_url}")
        text = extract_text_basic(fallback_url)
        if text:
            print(f"[text_extractor] Fallback URL succeeded: {fallback_url}")
            return text

    print(f"[text_extractor] All extraction methods failed for: {url}")
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
