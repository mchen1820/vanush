import asyncio
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import find_dotenv, load_dotenv
from flask import Flask, jsonify, request, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
FRONTEND_DIR = REPO_DIR / "frontend"
AGENTS_DIR = BASE_DIR / "agents"

# Allow imports from backend/agents without restructuring the project.
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from dedalus_labs import AsyncDedalus  # noqa: E402
from manager import manager_agent  # noqa: E402
from text_extractor import HEADERS, extract_pdf_bytes, extract_text  # noqa: E402


load_dotenv(find_dotenv())

app = Flask(__name__)


def json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def clamp_score(value, default: float = 0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def normalize_purpose(purpose: str | None) -> str:
    if not purpose:
        return "general credibility analysis"
    return purpose.strip() or "general credibility analysis"


def normalize_title(title: str | None) -> str | None:
    if not title:
        return None
    cleaned = re.sub(r"\s+", " ", title).strip()
    cleaned = re.sub(r"\s*[\-|–|—]\s*(SpringerLink|Springer Nature Link)$", "", cleaned, flags=re.IGNORECASE)
    if cleaned.upper() in {"REVIEW", "ARTICLE", "ABSTRACT"}:
        return None
    return cleaned or None


def parse_date_to_human(date_value: str | None) -> str | None:
    if not date_value:
        return None

    raw = date_value.strip()
    raw = re.sub(r"T.*$", "", raw)  # drop time for ISO values
    candidates = [raw]
    if "/" in raw:
        candidates.append(raw.replace("/", "-"))

    patterns = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%d %B %Y",
        "%B %d, %Y",
    ]

    for candidate in candidates:
        for pattern in patterns:
            try:
                dt = datetime.strptime(candidate, pattern)
                if pattern == "%Y":
                    return dt.strftime("%Y")
                if pattern == "%Y-%m":
                    return dt.strftime("%B %Y")
                return dt.strftime("%B %d, %Y")
            except ValueError:
                continue

    return date_value


def fetch_source_metadata(url: str) -> dict:
    """
    Extract metadata from publisher pages so UI title/author/date are accurate.
    Falls back gracefully if the source blocks access.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        response.raise_for_status()
    except Exception:
        return {}

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "html" not in content_type and "text" not in content_type:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")

    def meta_value(*selectors) -> str | None:
        for selector in selectors:
            tag = soup.select_one(selector)
            if tag and tag.get("content"):
                value = tag.get("content").strip()
                if value:
                    return value
        return None

    title = meta_value(
        "meta[name='citation_title']",
        "meta[property='og:title']",
        "meta[name='dc.title']",
    )
    if not title:
        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)

    authors = [
        tag.get("content").strip()
        for tag in soup.select("meta[name='citation_author']")
        if tag.get("content") and tag.get("content").strip()
    ]
    if not authors:
        creator = meta_value("meta[name='dc.creator']")
        if creator:
            authors = [creator]

    raw_date = meta_value(
        "meta[name='citation_online_date']",
        "meta[name='citation_publication_date']",
        "meta[property='article:published_time']",
        "meta[name='dc.date']",
    )

    return {
        "title": normalize_title(title),
        "authors": authors,
        "date": parse_date_to_human(raw_date),
    }


def guess_title_from_text(article_text: str) -> str:
    lines = [line.strip() for line in article_text.splitlines() if line.strip()]
    if not lines:
        return "Article"

    first = lines[0]
    first = re.sub(r"^(REVIEW|ARTICLE|ABSTRACT)\s+", "", first, flags=re.IGNORECASE)
    first = re.sub(r"\s+Received:.*$", "", first, flags=re.IGNORECASE)
    first = re.sub(r"\s+Accepted:.*$", "", first, flags=re.IGNORECASE)
    first = re.sub(r"\s+Published online:.*$", "", first, flags=re.IGNORECASE)
    first = re.sub(r"\s+©.*$", "", first)
    first = re.sub(r"\s+/C\d+.*$", "", first, flags=re.IGNORECASE)

    # Springer/PDF extraction often appends author names to title on one line.
    if "•" in first:
        first = first.split("•", 1)[0].strip()
    first = re.sub(
        r"\s+[A-Z][A-Za-z'´’.-]+\s+[A-Z][A-Za-z'´’.-]+\s*\d{0,2}$",
        "",
        first,
    )

    first = re.sub(r"\s+", " ", first).strip()
    return first[:180] if first else "Article"


def build_relevancy_check(citation_result: dict) -> dict:
    avg_age = citation_result.get("avg_citation_age_years")
    if avg_age is None:
        score = 60.0
        summary = "Publication date could not be verified precisely; relevancy appears moderate."
        notes = "Insufficient citation date metadata to confidently assess freshness."
        is_current = False
    else:
        score = clamp_score(100.0 - (float(avg_age) * 8.0), default=60.0)
        is_current = score >= 70.0
        summary = (
            f"Citation recency suggests {'current' if is_current else 'mixed recency'} references "
            f"(average age: {avg_age:.1f} years)."
        )
        notes = "Score is estimated from average citation age."

    return {
        "overall_score": round(score, 1),
        "confidence_score": 70.0,
        "summary": summary,
        "publication_date": "Unknown",
        "is_current": is_current,
        "relevancy_notes": notes,
    }


def build_organization_check(author_result: dict) -> dict:
    org_name = author_result.get("organization") or "Unknown organization"
    reliability = author_result.get("reliability_score_estimate")
    overall_score = clamp_score(reliability if reliability is not None else author_result.get("overall_score"), 60.0)
    bias_indicators = author_result.get("bias_indicators") or []

    strengths = []
    if author_result.get("author_name"):
        strengths.append(f"Identified author: {author_result['author_name']}")
    if author_result.get("total_articles_found") is not None:
        strengths.append(f"Prior publication footprint: {author_result['total_articles_found']} items")

    weaknesses = []
    if bias_indicators:
        weaknesses.append("Potential author/organization bias indicators were flagged")

    return {
        "overall_score": round(overall_score, 1),
        "confidence_score": clamp_score(author_result.get("confidence_score"), 65.0),
        "summary": f"Publisher/organization context assessed as {org_name}.",
        "structure_quality": "Derived from author/organization credibility signals.",
        "strengths": strengths,
        "weaknesses": weaknesses,
    }


def build_metadata(source: str, article_text: str, claim_result: dict, author_result: dict) -> dict:
    source_meta = fetch_source_metadata(source) if source.startswith("http") else {}
    title_guess = source_meta.get("title") or guess_title_from_text(article_text)
    parsed = urlparse(source) if source.startswith("http") else None
    source_host = parsed.netloc if parsed and parsed.netloc else "Direct input"

    author_from_source = ", ".join(source_meta.get("authors") or [])
    author_value = author_from_source or author_result.get("author_name") or "Unknown"
    date_value = source_meta.get("date") or datetime.now().strftime("%B %d, %Y")

    return {
        "title": title_guess,
        "author": author_value,
        "date": date_value,
        "preview_text": article_text[:500],
        "central_claim": claim_result.get("central_claim", ""),
        "article_summary": claim_result.get("summary", ""),
        "source": source_host,
    }


def format_results(results: dict, source: str, article_text: str) -> dict:
    claim = results["claim"].model_dump()
    citations = results["citations"].model_dump()
    bias = results["bias"].model_dump()
    author = results["author"].model_dump()
    evidence = results["evidence"].model_dump()
    usefulness = results["usefulness"].model_dump()
    synthesis = results["synthesis"].model_dump()

    overall_credibility = round(clamp_score(synthesis.get("overall_credibility_score"), 0.0))

    return {
        "metadata": build_metadata(source, article_text, claim, author),
        "overall_credibility": overall_credibility,
        "bias_check": bias,
        "author_credibility": author,
        "evidence_check": evidence,
        "usefulness_check": usefulness,
        "citation_check": citations,
        "organization_check": build_organization_check(author),
        "relevancy_check": build_relevancy_check(citations),
        "synthesis": synthesis,
    }


def require_api_key():
    api_key = os.getenv("DEDALUS_API_KEY")
    if not api_key:
        return None, json_error("DEDALUS_API_KEY is missing. Add it to your environment or .env file.", 500)
    return api_key, None


async def run_pipeline(article_text: str, topic: str) -> dict:
    api_key = os.getenv("DEDALUS_API_KEY")
    client = AsyncDedalus(api_key=api_key)
    return await manager_agent(client, input_text=article_text, topic=topic)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/<path:_subpath>", methods=["OPTIONS"])
def api_options(_subpath):
    return "", 204


@app.get("/api/health")
def health():
    has_key = bool(os.getenv("DEDALUS_API_KEY"))
    return jsonify({"status": "ok", "dedalus_api_key_loaded": has_key})


@app.post("/api/analyze/url")
def analyze_url():
    _, key_error = require_api_key()
    if key_error:
        return key_error

    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()
    topic = normalize_purpose(payload.get("purpose"))

    if not url:
        return json_error("Missing required field: url", 400)

    article_text = extract_text(url)
    if not article_text:
        return json_error("Could not extract article text from URL.", 422)

    try:
        results = asyncio.run(run_pipeline(article_text, topic))
        return jsonify(format_results(results, source=url, article_text=article_text))
    except Exception as exc:
        return json_error(f"Analysis failed: {exc}", 500)


@app.post("/api/analyze/text")
def analyze_text():
    _, key_error = require_api_key()
    if key_error:
        return key_error

    payload = request.get_json(silent=True) or {}
    article_text = (payload.get("text") or "").strip()
    topic = normalize_purpose(payload.get("purpose"))

    if len(article_text) < 100:
        return json_error("Text input is too short. Provide at least 100 characters.", 400)

    try:
        results = asyncio.run(run_pipeline(article_text, topic))
        return jsonify(format_results(results, source="text-input", article_text=article_text))
    except Exception as exc:
        return json_error(f"Analysis failed: {exc}", 500)


@app.post("/api/analyze/pdf")
def analyze_pdf():
    _, key_error = require_api_key()
    if key_error:
        return key_error

    upload = request.files.get("file") or request.files.get("pdf") or request.files.get("pdfFile")
    topic = normalize_purpose(request.form.get("purpose"))

    if upload is None:
        return json_error("Missing uploaded file under form field 'file'.", 400)

    file_bytes = upload.read()
    if not file_bytes:
        return json_error("Uploaded file is empty.", 400)

    article_text = extract_pdf_bytes(file_bytes, url=upload.filename or "uploaded.pdf")
    if not article_text:
        return json_error("Could not extract readable text from the PDF.", 422)

    try:
        results = asyncio.run(run_pipeline(article_text, topic))
        return jsonify(format_results(results, source=upload.filename or "uploaded.pdf", article_text=article_text))
    except Exception as exc:
        return json_error(f"Analysis failed: {exc}", 500)


@app.get("/")
def serve_index():
    if FRONTEND_DIR.exists():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"message": "Vanush API running"})


@app.get("/<path:path>")
def serve_frontend_file(path: str):
    if path.startswith("api/"):
        return json_error("Route not found", 404)
    if FRONTEND_DIR.exists() and (FRONTEND_DIR / path).exists():
        return send_from_directory(FRONTEND_DIR, path)
    if FRONTEND_DIR.exists():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return json_error("Frontend not found", 404)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    debug = os.getenv("FLASK_DEBUG", "1") != "0"
    app.run(host="0.0.0.0", port=port, debug=debug)
