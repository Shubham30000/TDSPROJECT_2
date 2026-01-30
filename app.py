# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "python-dotenv",
#   "requests",
#   "fastapi",
#   "uvicorn[standard]",
#   "playwright",
#   "beautifulsoup4",
#   "lxml",
#   "pypdf",
#   "matplotlib"
# ]
# ///

"""
PRODUCTION VERSION: Complete implementation with HTTP 400 handling and retry logic
"""

import os
import json
import sys
import re
import time
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks
from scraper import scrape_quiz_page
import subprocess

 
load_dotenv()

# Handle both local .env and HuggingFace Secrets
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN") or os.getenv("AIPIPE_TOKEN_SECRET")
AIPIPE_URL = os.getenv("AIPIPE_API_URL") or os.getenv("AIPIPE_API_URL_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY_SECRET")

if not AIPIPE_TOKEN or not AIPIPE_URL or not SECRET_KEY:
    print("⚠️  WARNING: Missing environment variables!")
    print(f"   AIPIPE_TOKEN: {'✓' if AIPIPE_TOKEN else '✗'}")
    print(f"   AIPIPE_URL: {'✓' if AIPIPE_URL else '✗'}")
    print(f"   SECRET_KEY: {'✓' if SECRET_KEY else '✗'}")


app = FastAPI()


def extract_base_url(url: str) -> str:
    """Extract base URL (scheme + netloc) from a full URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def make_absolute_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute using base URL."""
    if url.startswith('http'):
        return url
    return urljoin(base_url, url)


def process_request(data):
    """Process quiz requests in background."""
    print("Processing request in background for:", data.get("email"))

    quiz_url = data.get("url")
    if not quiz_url:
        print("[process_request] No URL in data, aborting")
        return

    # Process quiz chain with 3-minute overall timeout
    max_quizzes = 10
    quiz_count = 0
    base_url = extract_base_url(quiz_url)
    overall_start_time = time.time()
    overall_timeout = 180  # 3 minutes total
    
    while quiz_url and quiz_count < max_quizzes:
        # Check overall timeout
        elapsed = time.time() - overall_start_time
        if elapsed > overall_timeout:
            print(f"\n[process_request] ⏱️  Overall timeout reached ({elapsed:.1f}s)")
            break
        
        quiz_count += 1
        print(f"\n{'='*70}")
        print(f"PROCESSING QUIZ {quiz_count}: {quiz_url}")
        print(f"Time remaining: {overall_timeout - elapsed:.1f}s")
        print(f"{'='*70}\n")
        
        next_url = process_single_quiz(data, quiz_url, base_url, overall_start_time, overall_timeout)
        
        if next_url:
            # Convert relative URLs to absolute
            next_url = make_absolute_url(next_url, base_url)
            print(f"\n[process_request] ✓ Got next quiz URL: {next_url}")
            quiz_url = next_url
        else:
            print(f"\n[process_request] ✓ Quiz chain completed!")
            break
    
    print(f"\n[process_request] Finished processing {quiz_count} quiz(s)")


def process_single_quiz(data: dict, quiz_url: str, base_url: str, overall_start_time: float, overall_timeout: float) -> str | None:
    """
    Process a single quiz with retry logic.
    Returns the next quiz URL if any, or None if quiz chain ends.
    """
    
    max_attempts = 3
    
    for attempt in range(1, max_attempts + 1):
        # Check if we've exceeded overall timeout
        elapsed = time.time() - overall_start_time
        if elapsed > overall_timeout:
            print(f"[process_single_quiz] ⏱️  Overall timeout exceeded")
            return None
        
        print(f"\n[Attempt {attempt}/{max_attempts}]")
        
        # 1) Scrape the quiz page
        try:
            quiz_data = scrape_quiz_page(quiz_url)
        except Exception as e:
            print(f"[process_single_quiz] Error scraping: {e}")
            if attempt < max_attempts:
                print("Retrying...")
                time.sleep(2)
                continue
            return None

        quiz_text = quiz_data["quiz_text"]
        submit_url = quiz_data["submit_url"]
        file_urls = quiz_data["file_urls"]
        all_links = quiz_data["all_links"]
        
        # Default submit URL if none detected
        if not submit_url:
            submit_url = f"{base_url}/submit"
            print(f"[process_single_quiz] Using default submit URL: {submit_url}")
        else:
            # Ensure submit URL is absolute
            submit_url = make_absolute_url(submit_url, base_url)
        
        # Convert all file URLs to absolute
        file_urls = [make_absolute_url(url, base_url) for url in file_urls]
        
        # Extract any page URLs from links (for scraping tasks)
        page_urls = [link for link in all_links if not link.endswith(('.csv', '.json', '.pdf'))]
        page_urls = [make_absolute_url(url, base_url) for url in page_urls if url != submit_url]
        
        print("[process_single_quiz] Scraper summary:")
        print("  submit_url  :", submit_url)
        print("  file_urls   :", file_urls)
        print("  page_urls   :", page_urls)
        print("  total links :", len(all_links))

        # 2) Build prompt with CODE TEMPLATES
        prompt_for_llm = f"""You are a code generator. Read the quiz and choose the correct template.

**QUIZ INSTRUCTIONS:**
\"\"\"
{quiz_text}
\"\"\"

**AVAILABLE URLS:**
- Base URL: {base_url}
- Submit URL: {submit_url}
- File URLs: {json.dumps(file_urls)}
- Page URLs: {json.dumps(page_urls)}

---

**IDENTIFY THE QUIZ TYPE AND USE THE TEMPLATE:**

**1. CSV WITH NO HEADERS (file contains only numbers)**

If quiz mentions "cutoff" or "sum of numbers >= X":

```python
import httpx

# Download CSV - USE ABSOLUTE URL FROM file_urls
csv_url = "{file_urls[0] if file_urls else 'REPLACE_WITH_CSV_URL'}"
text = httpx.get(csv_url).text
print(f"CSV Content: {{text}}")

# Parse as numbers (NO HEADERS)
lines = text.strip().split('\\n')
numbers = [int(line.strip()) for line in lines if line.strip()]
print(f"Parsed numbers: {{numbers}}")

# Apply cutoff logic (extract cutoff from quiz text)
cutoff = 500  # REPLACE WITH ACTUAL CUTOFF from quiz
result = sum(n for n in numbers if n >= cutoff)

print(f"FINAL_ANSWER: {{result}}")
```

**2. CSV WITH HEADERS (for visualization)**

If quiz asks to "create a BAR CHART":

```python
import httpx
import csv
from io import StringIO
from data_tools import create_bar_chart

# Download CSV - USE ABSOLUTE URL
csv_url = "{file_urls[0] if file_urls else 'REPLACE_WITH_CSV_URL'}"
text = httpx.get(csv_url).text

# Parse CSV with headers
reader = csv.DictReader(StringIO(text))
data = list(reader)
print(f"Data: {{data}}")

# Extract columns (adjust keys based on actual headers)
labels = [row['category'] for row in data]
values = [float(row['value']) for row in data]

# Create chart
chart = create_bar_chart(
    labels=labels,
    values=values,
    title="Chart Title",
    xlabel="Category",
    ylabel="Value"
)

print(f"FINAL_ANSWER: {{chart}}")
```

**3. JSON API**

If quiz mentions "API" or "fetch data":

```python
import httpx

# USE ABSOLUTE API URL
api_url = "{base_url}/api/sales"  # ADJUST path as needed
response = httpx.get(api_url)
data = response.json()
print(f"API Response: {{data}}")

# Example: sum revenue for active products
if isinstance(data, dict) and "products" in data:
    products = data["products"]
    result = sum(p["revenue"] for p in products if p.get("status") == "active")
else:
    result = data  # If direct value

print(f"FINAL_ANSWER: {{result}}")
```

**4. WEB SCRAPING**

If quiz asks to "extract secret code" or "find value in page":

```python
import httpx
from bs4 import BeautifulSoup

# USE ABSOLUTE PAGE URL
page_url = "{page_urls[0] if page_urls else base_url + '/secret-page'}"  # ADJUST as needed
html = httpx.get(page_url).text
soup = BeautifulSoup(html, 'html.parser')

# Remove noise
for tag in soup(['script', 'style']):
    tag.decompose()

# Find the value (look in <strong>, <code>, etc.)
result = None
for tag in soup.find_all(['strong', 'code', 'b', 'span']):
    text = tag.get_text(strip=True)
    if text and len(text) >= 3:
        result = text
        break

print(f"FINAL_ANSWER: {{result}}")
```

**5. SIMPLE MATH**

If quiz asks "What is X + Y?" or "What is X * Y?":

```python
# Extract numbers and operator from quiz
# Example: "What is 10 + 20?"
result = 10 + 20

print(f"FINAL_ANSWER: {{result}}")
```

---

**CRITICAL RULES:**
1. ALL URLs must be ABSOLUTE (start with http://)
2. Use the provided base_url, file_urls, and page_urls
3. NO relative URLs like "/api/sales" - use "{base_url}/api/sales"
4. Output ONLY Python code
5. NO markdown backticks, NO explanations
6. The code must print "FINAL_ANSWER: <value>"
"""

        # 3) Call LLM
        try:
            llm_response = httpx.post(
                AIPIPE_URL,
                headers={
                    "accept": "*/*",
                    "accept-language": "en-US,en;q=0.9",
                    "authorization": f"Bearer {AIPIPE_TOKEN}",
                    "content-type": "application/json",
                },
                json={
                    "model": "openai/gpt-4o-mini",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a code generator. Output ONLY Python code. No explanations, no markdown, no backticks. Just executable Python code.",
                        },
                        {"role": "user", "content": prompt_for_llm},
                    ],
                },
                timeout=60,
            )
            llm_response.raise_for_status()
            answer_script = llm_response.json()
        except Exception as e:
            print(f"[process_single_quiz] Error calling LLM: {e}")
            if attempt < max_attempts:
                print("Retrying...")
                time.sleep(2)
                continue
            return None

        # 4) Execute script
        try:
            script_code = answer_script["choices"][0]["message"]["content"]
            
            # Clean markdown (in case LLM ignores instructions)
            if "```python" in script_code:
                script_code = script_code.split("```python")[1].split("```")[0].strip()
            elif "```" in script_code:
                script_code = script_code.split("```")[1].split("```")[0].strip()
            
            # Remove common prefixes
            if script_code.startswith("python"):
                script_code = "\n".join(script_code.split("\n")[1:])
            
            with open("generated_script.py", "w", encoding="utf-8") as f:
                f.write(script_code)
            
            print("[process_single_quiz] Generated code:")
            print("="*70)
            print(script_code)
            print("="*70)
            
            complete_process = subprocess.run(
                [sys.executable, "generated_script.py"],
                capture_output=True,
                text=True,
                env=os.environ.copy(),
                timeout=120,
            )

            stdout = complete_process.stdout
            stderr = complete_process.stderr

            print("\n===== EXECUTION OUTPUT =====")
            print(stdout)
            if stderr:
                print("===== STDERR =====")
                print(stderr)
            print(f"===== Exit code: {complete_process.returncode} =====\n")
            
            # Extract answer
            answer_value = None
            for line in stdout.splitlines():
                if "FINAL_ANSWER:" in line:
                    answer_value = line.split("FINAL_ANSWER:", 1)[1].strip()
                    print(f"✓ Extracted answer: {answer_value[:100]}{'...' if len(answer_value) > 100 else ''}")
                    break
            
            if not answer_value:
                print("✗ ERROR: No FINAL_ANSWER found in output")
                if attempt < max_attempts:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return None
            
            # Parse answer type
            if answer_value.startswith('{') or answer_value.startswith('['):
                try:
                    answer_value = json.loads(answer_value)
                except:
                    pass
            elif answer_value.replace('.', '').replace('-', '').isdigit():
                try:
                    answer_value = float(answer_value) if '.' in answer_value else int(answer_value)
                except:
                    pass
            
            payload = {
                "email": data.get("email"),
                "secret": data.get("secret"),
                "url": quiz_url,
                "answer": answer_value,
            }
            
            print(f"\n📤 Submitting to: {submit_url}")
            print(f"📋 Payload: {json.dumps(payload, indent=2)}")
            
            try:
                resp = httpx.post(submit_url, json=payload, timeout=60.0)
                resp_text = resp.text
                print(f"\n📥 Server response [{resp.status_code}]: {resp_text}")
                
                # Parse response
                try:
                    response_data = resp.json()
                    is_correct = response_data.get("correct", False)
                    next_url = response_data.get("url")
                    reason = response_data.get("reason", "")
                    
                    if is_correct:
                        print(f"✅ CORRECT! {response_data.get('message', '')}")
                        return next_url  # Success - return next URL or None
                    else:
                        print(f"❌ INCORRECT: {reason or response_data.get('message', 'Wrong answer')}")
                        
                        # If we have a next URL even though wrong, we can skip to it
                        if next_url:
                            print(f"⏭️  Server provided next URL despite wrong answer: {next_url}")
                            return next_url
                        
                        # Otherwise retry if we have attempts left
                        if attempt < max_attempts:
                            print(f"🔄 Retrying... (Attempt {attempt + 1}/{max_attempts})")
                            time.sleep(2)
                            continue
                        else:
                            print(f"❌ Max attempts reached. Moving on.")
                            return None
                
                except Exception as parse_error:
                    print(f"⚠️  Could not parse response: {parse_error}")
                    if attempt < max_attempts:
                        print("Retrying...")
                        time.sleep(2)
                        continue
                    return None
                
            except Exception as e:
                print(f"✗ Submission error: {e}")
                if attempt < max_attempts:
                    print("Retrying...")
                    time.sleep(2)
                    continue
                return None
            
        except subprocess.TimeoutExpired:
            print("✗ Script execution timed out (120s)")
            if attempt < max_attempts:
                print("Retrying...")
                time.sleep(2)
                continue
            return None
        except Exception as e:
            print(f"✗ Execution error: {e}")
            import traceback
            traceback.print_exc()
            if attempt < max_attempts:
                print("Retrying...")
                time.sleep(2)
                continue
            return None
    
    # All attempts exhausted
    print(f"❌ Failed after {max_attempts} attempts")
    return None


@app.post("/receive_request")
async def receive_request(request: Request, background_tasks: BackgroundTasks):
    """
    Main endpoint to receive quiz requests.
    
    Returns:
    - 200: Valid request accepted
    - 400: Invalid JSON payload
    - 403: Invalid secret key
    """
    
    # HTTP 400 HANDLING - Invalid JSON
    try:
        data = await request.json()
    except Exception as e:
        print(f"[receive_request] Invalid JSON received: {e}")
        return JSONResponse(
            status_code=400,
            content={"message": "Bad Request: Invalid JSON payload"}
        )
    
    # HTTP 403 HANDLING - Invalid secret
    if data.get("secret") != SECRET_KEY:
        print(f"[receive_request] Invalid secret: {data.get('secret')}")
        return JSONResponse(
            status_code=403, 
            content={"message": "Forbidden: Invalid secret"}
        )
    
    # Valid request - process in background
    print(f"[receive_request] ✓ Valid request from {data.get('email')}")
    background_tasks.add_task(process_request, data)
    
    return JSONResponse(
        status_code=200, 
        content={
            "message": "Request received successfully", 
            "data": data
        }
    )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "LLM Quiz Solver",
        "version": "1.0.0",
        "features": [
            "HTTP 400 handling for invalid JSON",
            "HTTP 403 for invalid secrets",
            "Retry logic (up to 3 attempts per quiz)",
            "3-minute overall timeout",
            "Quiz chain support (up to 10 sequential quizzes)",
            "Visualization support (matplotlib charts)"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    print(f"🚀 Starting quiz automation server on http://0.0.0.0:{port}")
    print(f"✅ HTTP 400/403 error handling enabled")
    print(f"✅ Retry logic: up to 3 attempts per quiz")
    print(f"✅ Overall timeout: 3 minutes per request")
    print(f"✅ Visualization support included")
    uvicorn.run(app, host="0.0.0.0", port=port)