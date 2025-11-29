# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "playwright",
#   "beautifulsoup4",
#   "lxml"
# ]
# ///

"""
Pure scraping pipeline - test this independently before integrating.
Usage: python scraper.py <url>
"""

import sys
import re
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


# ============================================================================
# CORE SCRAPING FUNCTIONS
# ============================================================================

def fetch_static_html(url: str, timeout: float = 15.0) -> str | None:
    """
    Fetch HTML using simple HTTP (for static pages).
    
    Args:
        url: Target URL
        timeout: Request timeout in seconds
        
    Returns:
        HTML string or None if failed
    """
    try:
        print(f"[Static] Fetching {url}")
        resp = httpx.get(
            url, 
            timeout=timeout, 
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        resp.raise_for_status()
        print(f"[Static] ✓ Got {len(resp.text)} chars")
        return resp.text
    except Exception as e:
        print(f"[Static] ✗ Failed: {e}")
        return None


def fetch_dynamic_html(url: str, timeout: float = 30.0, wait_for_selector: str = None) -> str | None:
    """
    Fetch HTML using Playwright (for JavaScript-rendered pages).
    
    Args:
        url: Target URL
        timeout: Page load timeout in seconds
        wait_for_selector: Optional CSS selector to wait for before capturing
        
    Returns:
        Rendered HTML string or None if failed
    """
    try:
        print(f"[Playwright] Launching browser for {url}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            # Navigate and wait for network to be idle
            page.goto(url, wait_until="networkidle", timeout=int(timeout * 1000))
            
            # If specific selector provided, wait for it
            if wait_for_selector:
                print(f"[Playwright] Waiting for selector: {wait_for_selector}")
                page.wait_for_selector(wait_for_selector, timeout=5000)
            
            # Extra time for any delayed JS execution
            page.wait_for_timeout(2000)
            
            html = page.content()
            browser.close()
            
        print(f"[Playwright] ✓ Got {len(html)} chars")
        return html
        
    except Exception as e:
        print(f"[Playwright] ✗ Failed: {e}")
        return None


# ============================================================================
# INTELLIGENT CONTENT EXTRACTION
# ============================================================================

def extract_quiz_data(html: str, base_url: str) -> dict:
    """
    Extract all relevant quiz information from HTML.
    Handles both absolute URLs and relative paths.
    
    Returns dict with:
        - quiz_text: The main quiz question/instructions
        - submit_url: Where to POST the answer
        - file_urls: List of downloadable files (PDF, CSV, etc.)
        - all_links: All URLs found on page
        - form_data: Any form fields detected
    """
    soup = BeautifulSoup(html, "lxml")
    
    # ===== STEP 1: Find Quiz Text (IMPROVED - Get ALL visible text) =====
    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()
    
    # Get the body or whole document
    body = soup.body if soup.body else soup
    
    # Get ALL visible text, preserving structure with newlines
    quiz_text = body.get_text("\n", strip=True)
    
    # Clean up excessive whitespace while preserving line breaks
    lines = [line.strip() for line in quiz_text.split("\n")]
    lines = [line for line in lines if line]  # Remove empty lines
    quiz_text = "\n".join(lines)
    
    print(f"[Extract] Extracted {len(quiz_text)} chars of text")
    
    # ===== STEP 2: Extract All URLs (ABSOLUTE + RELATIVE) =====
    all_links = set()
    
    # Get full page text for URL extraction
    full_text = quiz_text
    
    # Pattern 1: Absolute URLs (http/https)
    absolute_url_pattern = r'https?://[^\s"\'\)<>\]}\u201d\u201c]+'
    for match in re.findall(absolute_url_pattern, full_text):
        all_links.add(match)
        print(f"[Extract] Found absolute URL: {match}")
    
    # Pattern 2: Relative paths mentioned after keywords
    # Matches: "POST to /submit", "submit to /answer", etc.
    relative_path_pattern = r'(?:POST|GET|to|:)\s*["\']?\s*(/[\w\-/.]+)'
    for match in re.findall(relative_path_pattern, full_text, re.IGNORECASE):
        # Clean up the path
        path = match.strip().strip('"\'').strip()
        if path.startswith('/') and len(path) > 1:
            # Convert to absolute URL
            full_url = urljoin(base_url, path)
            all_links.add(full_url)
            print(f"[Extract] Found relative path: {path} -> {full_url}")
    
    # Pattern 3: Paths in JSON-like structures
    # Matches: "url": "/demo", "endpoint": "/submit"
    json_path_pattern = r'["\'](?:url|endpoint|path|action)["\']?\s*:\s*["\']?(/[\w\-/.]+)["\']?'
    for match in re.findall(json_path_pattern, full_text, re.IGNORECASE):
        path = match.strip().strip('"\'').strip()
        if path.startswith('/') and len(path) > 1:
            full_url = urljoin(base_url, path)
            all_links.add(full_url)
            print(f"[Extract] Found JSON path: {path} -> {full_url}")
    
    # Pattern 4: Standalone paths (on their own line or after whitespace)
    # Be more aggressive - find paths that look like API endpoints
    standalone_path_pattern = r'[\s\n](/[a-zA-Z][\w\-/]*)'
    for match in re.findall(standalone_path_pattern, full_text):
        path = match.strip()
        # Filter: must be reasonable length, look like an endpoint
        if 2 <= len(path) <= 50 and not any(x in path for x in ['\\', '..', ' ', '(', ')']):
            # Skip if it looks like a file path (has extension not in our list)
            if '.' in path.split('/')[-1]:
                ext = path.split('.')[-1].lower()
                if ext not in ['json', 'html', 'xml', 'txt', 'csv', 'pdf']:
                    continue
            full_url = urljoin(base_url, path)
            all_links.add(full_url)
            print(f"[Extract] Found standalone path: {path} -> {full_url}")
    
    # From HTML <a> tags
    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        all_links.add(full_url)
        print(f"[Extract] Found <a> link: {full_url}")

    # From <link> tags
    for link in soup.find_all("link", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        all_links.add(full_url)
    
    all_links = sorted(all_links)
    
    # ===== STEP 3: Identify Submit URL (FIXED) =====
    submit_url = None
    file_extensions = ['.pdf', '.csv', '.txt', '.json', '.xlsx', '.xls', '.xml', '.zip']
    
    # Strategy 1: Look for "POST to /path" or "POST your answer to /path" patterns
    post_patterns = [
        r'post\s+(?:this\s+)?(?:json\s+)?(?:to|your\s+answer\s+to)\s*[:\s]*["\']?\s*(https?://[^\s"\'<>)]+|/[\w\-/.]+)',
        r'submit\s+(?:to\s+|your\s+answer\s+to\s+)?[:\s]*["\']?\s*(https?://[^\s"\'<>)]+|/[\w\-/.]+)',
        r'send\s+(?:to\s+)?[:\s]*["\']?\s*(https?://[^\s"\'<>)]+|/[\w\-/.]+)',
    ]
    
    text_lower = full_text.lower()
    for pattern in post_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
        if matches:
            for match in matches:
                # Clean the match
                path = match.strip().strip('"\'').strip()
                
                # Skip if it's a file (has file extension)
                if any(path.lower().endswith(ext) for ext in file_extensions):
                    print(f"[Extract] Skipping file URL as submit target: {path}")
                    continue
                
                # Build the full URL
                if path.startswith('http'):
                    # Already absolute
                    potential_url = path
                elif path.startswith('/'):
                    # Relative path
                    potential_url = urljoin(base_url, path)
                else:
                    continue
                
                # Verify this looks like a submit endpoint
                if potential_url in all_links:
                    submit_url = potential_url
                    print(f"[Extract] ✓ Found submit URL via POST pattern: {submit_url}")
                    break
            if submit_url:
                break
    
    # Strategy 2: Look for <form action="...">
    if not submit_url:
        forms = soup.find_all("form")
        for form in forms:
            action = form.get("action")
            if action:
                # Skip empty actions or just "#"
                if action and action != "#":
                    full_url = urljoin(base_url, action)
                    # Make sure it's not a file
                    if not any(full_url.lower().endswith(ext) for ext in file_extensions):
                        submit_url = full_url
                        print(f"[Extract] ✓ Found submit URL via <form action>: {submit_url}")
                        break
    
    # Strategy 3: Look for URLs with "submit" keyword in the path
    if not submit_url:
        submit_keywords = ["submit", "answer", "response", "check", "verify"]
        for url in all_links:
            url_lower = url.lower()
            # Skip file URLs
            if any(url_lower.endswith(ext) for ext in file_extensions):
                continue
            # Check for submit keywords
            if any(keyword in url_lower for keyword in submit_keywords):
                submit_url = url
                print(f"[Extract] ✓ Found submit URL via keyword in path: {submit_url}")
                break
    
    # Strategy 4: CONSERVATIVE - Only if clear evidence
    # Do NOT guess if unclear - let LLM infer from quiz text
    if not submit_url:
        print(f"[Extract] ⚠ No clear submit URL found. LLM will need to infer from quiz text.")
        print(f"[Extract] Available non-file URLs: {[u for u in all_links if not any(u.lower().endswith(ext) for ext in file_extensions)]}")
    
    # ===== STEP 4: Identify File URLs =====
    file_urls = []
    
    for url in all_links:
        url_lower = url.lower()
        # Exclude the submit URL from file URLs
        if url == submit_url:
            continue
        if any(url_lower.endswith(ext) for ext in file_extensions):
            file_urls.append(url)
    
    # ===== STEP 5: Extract Form Data (if any) =====
    form_data = {}
    forms = soup.find_all("form")
    if forms:
        form = forms[0]  # Take first form
        form_data["action"] = urljoin(base_url, form.get("action", ""))
        form_data["method"] = form.get("method", "POST").upper()
        
        # Get all input fields
        inputs = {}
        for inp in form.find_all(["input", "textarea", "select"]):
            name = inp.get("name")
            value = inp.get("value", "")
            if name:
                inputs[name] = value
        form_data["inputs"] = inputs
    
    print(f"\n[Extract] Summary:")
    print(f"  - Quiz text: {len(quiz_text)} chars")
    print(f"  - Submit URL: {submit_url}")
    print(f"  - File URLs: {len(file_urls)} found")
    print(f"  - Total links: {len(all_links)}")
    
    return {
        "quiz_text": quiz_text,
        "submit_url": submit_url,
        "file_urls": file_urls,
        "all_links": list(all_links),  # Convert to list for JSON serialization
        "form_data": form_data,
    }


# ============================================================================
# MAIN SCRAPING PIPELINE
# ============================================================================

def scrape_quiz_page(url: str) -> dict:
    """
    Main scraping function with automatic fallback strategy.
    
    Strategy:
    1. Try static HTTP first (faster)
    2. If content looks insufficient, try Playwright
    3. Extract all quiz data intelligently
    
    Returns:
        dict with quiz data and metadata
    """
    print(f"\n{'='*70}")
    print(f"SCRAPING: {url}")
    print(f"{'='*70}\n")
    
    html = None
    source = None
    
    # ATTEMPT 1: Static fetch
    html = fetch_static_html(url)
    if html and len(html) > 500:
        # Quick check: does it look like it has content?
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text().strip()
        
        if len(text) > 100:
            print("[Pipeline] ✓ Static HTML looks good")
            source = "static"
        else:
            print("[Pipeline] Static HTML too minimal, trying Playwright...")
            html = None
    
    # ATTEMPT 2: Playwright fallback
    if not html:
        # Try waiting for common content selectors
        for selector in ["#result", "#content", ".quiz", "main", "article"]:
            html = fetch_dynamic_html(url, wait_for_selector=selector)
            if html:
                source = f"playwright (waited for {selector})"
                break
        
        # Last resort: no specific selector
        if not html:
            html = fetch_dynamic_html(url)
            if html:
                source = "playwright (no selector)"
    
    if not html:
        raise RuntimeError(f"Failed to fetch {url} using both static and dynamic methods")
    
    # Extract all quiz data
    print(f"\n[Pipeline] Extracting quiz data...")
    quiz_data = extract_quiz_data(html, base_url=url)
    quiz_data["source"] = source
    quiz_data["original_url"] = url
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"EXTRACTION RESULTS")
    print(f"{'='*70}")
    print(f"Source: {source}")
    print(f"Quiz text length: {len(quiz_data['quiz_text'])} chars")
    print(f"Submit URL: {quiz_data['submit_url']}")
    print(f"File URLs: {len(quiz_data['file_urls'])} found")
    for f in quiz_data['file_urls']:
        print(f"  - {f}")
    print(f"Total links: {len(quiz_data['all_links'])}")
    print(f"\n--- QUIZ TEXT (first 500 chars) ---")
    print(quiz_data['quiz_text'][:500])
    if len(quiz_data['quiz_text']) > 500:
        print("...")
    print(f"{'='*70}\n")
    
    return quiz_data


# ============================================================================
# TESTING & CLI
# ============================================================================

def test_scraper():
    """Test the scraper with the demo URL."""
    demo_url = "https://tds-llm-analysis.s-anand.net/demo"
    
    print("Testing scraper with demo URL...")
    try:
        result = scrape_quiz_page(demo_url)
        
        print("\n✓ SCRAPING TEST PASSED")
        print(f"  Found submit URL: {result['submit_url'] is not None}")
        print(f"  Found quiz text: {len(result['quiz_text'])} chars")
        print(f"  Found files: {len(result['file_urls'])}")
        
        return result
    except Exception as e:
        print(f"\n✗ SCRAPING TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Install playwright if needed
    import subprocess
    print("Ensuring Playwright is installed...")
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=False,
        capture_output=True
    )
    
    # Check if URL provided as argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        try:
            result = scrape_quiz_page(url)
            
            # Save result to file for inspection
            import json
            output_file = "scraper_output.json"
            with open(output_file, "w") as f:
                # Make it JSON serializable
                output = {
                    "quiz_text": result["quiz_text"],
                    "submit_url": result["submit_url"],
                    "file_urls": result["file_urls"],
                    "all_links": result["all_links"],
                    "source": result["source"],
                    "original_url": result["original_url"]
                }
                json.dump(output, f, indent=2)
            
            print(f"\n✓ Results saved to {output_file}")
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # Run test with demo URL
        test_scraper()