# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pypdf",
#   "matplotlib",
#   "pillow"
# ]
# ///

"""
Enhanced utility functions for quiz scripts:
- downloading files (text / binary)
- reading CSV / JSON
- extracting text from PDFs
- basic text cleaning
- VISUALIZATION: creating charts and returning base64
"""

from __future__ import annotations
import io
import csv
import json
import base64
from typing import List, Dict, Any

import httpx
from pypdf import PdfReader


# ----------------------- HTTP HELPERS ----------------------- #

def download_bytes(url: str, timeout: float = 30.0) -> bytes:
    """Download binary content from URL."""
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.content


def download_text(url: str, timeout: float = 30.0, encoding: str | None = None) -> str:
    """Download text content from URL."""
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
            page.wait_for_timeout(5000)
            
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        raise RuntimeError(f"Failed to fetch JS-rendered page: {e}")


# ----------------------- VISUALIZATION ---------------------- #

def create_bar_chart(
    labels: List[str],
    values: List[float],
    title: str = "Bar Chart",
    xlabel: str = "Categories",
    ylabel: str = "Values",
    color: str = "steelblue"
) -> str:
    """
    Create a bar chart and return as base64 data URI.
    
    Args:
        labels: List of category labels
        values: List of numeric values
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Bar color
    
    Returns:
        Base64 data URI string: "data:image/png;base64,..."
    """
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values, color=color)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    # Rotate x labels if many categories
    if len(labels) > 5:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save to bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    # Convert to base64
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


def create_line_chart(
    x_values: List[float],
    y_values: List[float],
    title: str = "Line Chart",
    xlabel: str = "X",
    ylabel: str = "Y",
    color: str = "steelblue"
) -> str:
    """
    Create a line chart and return as base64 data URI.
    
    Args:
        x_values: X-axis values
        y_values: Y-axis values
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        color: Line color
    
    Returns:
        Base64 data URI string
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x_values, y_values, color=color, linewidth=2, marker='o')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


def create_pie_chart(
    labels: List[str],
    values: List[float],
    title: str = "Pie Chart"
) -> str:
    """
    Create a pie chart and return as base64 data URI.
    
    Args:
        labels: Category labels
        values: Numeric values
        title: Chart title
    
    Returns:
        Base64 data URI string
    """
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return f"data:image/png;base64,{img_base64}"


# ----------------------- HELPER FUNCTIONS ------------------- #

def encode_image_to_base64(image_path: str) -> str:
    """
    Read an image file and convert to base64 data URI.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Base64 data URI string
    """
    with open(image_path, 'rb') as f:
        img_bytes = f.read()
    
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Detect image type from extension
    ext = image_path.lower().split('.')[-1]
    mime_type = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }.get(ext, 'image/png')
    
    return f"data:{mime_type};base64,{img_base64}"