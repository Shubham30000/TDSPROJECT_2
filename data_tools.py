# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pypdf"
# ]
# ///

"""
Utility functions for quiz scripts:
- downloading files (text / binary)
- reading CSV / JSON
- extracting text from PDFs
- basic text cleaning
"""

from __future__ import annotations
import io
import csv
import json
from typing import List, Dict, Any

import httpx
from pypdf import PdfReader


# ----------------------- HTTP HELPERS ----------------------- #

def download_bytes(url: str, timeout: float = 30.0) -> bytes:
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.content


def download_text(url: str, timeout: float = 30.0, encoding: str | None = None) -> str:
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    if encoding:
        resp.encoding = encoding
    return resp.text


# ----------------------- CSV / JSON ------------------------- #

def read_csv_from_url(url: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
    """
    Download CSV and return list of dict rows.
    """
    text = download_text(url, timeout=timeout)
    f = io.StringIO(text)
    reader = csv.DictReader(f)
    return list(reader)


def read_json_from_url(url: str, timeout: float = 30.0) -> Any:
    """
    Download JSON and return parsed object.
    """
    text = download_text(url, timeout=timeout)
    return json.loads(text)


# ----------------------- PDF TEXT --------------------------- #

def read_pdf_from_url(url: str, timeout: float = 30.0) -> str:
    """
    Download a PDF file and extract all text as one big string.
    """
    pdf_bytes = download_bytes(url, timeout=timeout)
    reader = PdfReader(io.BytesIO(pdf_bytes))

    pages_text: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        pages_text.append(t)

    return "\n".join(pages_text)


# ----------------------- TEXT CLEANING ---------------------- #

def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/newlines, strip ends."""
    import re
    return re.sub(r"\s+", " ", text).strip()


def to_lower(text: str) -> str:
    return text.lower()


def clean_text_block(text: str) -> str:
    """
    Convenience: lowercase + normalize whitespace.
    """
    return normalize_whitespace(text).lower()


# ----------------------- PLAYWRIGHT HELPER ---------------------- #
def fetch_js_rendered_page(url: str, timeout: float = 30.0) -> str:
    """
    Fetch a JavaScript-rendered page using Playwright.
    Returns the rendered HTML as a string.
    
    Use this when a page uses JavaScript to load content.
    """
    from playwright.sync_api import sync_playwright
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            
            # Wait longer for JS to execute
            page.wait_for_timeout(5000)  # Changed from 2000 to 5000
            
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        raise RuntimeError(f"Failed to fetch JS-rendered page: {e}")