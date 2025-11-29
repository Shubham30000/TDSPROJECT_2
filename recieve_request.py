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
#   "pypdf"
# ]
# ///


import os
import json
import sys
import re
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks
from scraper import scrape_quiz_page
import subprocess

 
load_dotenv()

AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
AIPIPE_URL = os.getenv("AIPIPE_API_URL")
SECRET_KEY = os.getenv("SECRET_KEY")


app = FastAPI()


def process_request(data):
    """
    Regular function (not async) to avoid Playwright sync API conflicts.
    Playwright's sync API cannot run inside an asyncio event loop.
    """
    print("Processing request in background for:", data.get("email"))

    quiz_url = data.get("url")
    if not quiz_url:
        print("[process_request] No URL in data, aborting")
        return

    # Process quiz chain (handle multiple quizzes in sequence)
    max_quizzes = 10  # Safety limit
    quiz_count = 0
    
    while quiz_url and quiz_count < max_quizzes:
        quiz_count += 1
        print(f"\n{'='*70}")
        print(f"PROCESSING QUIZ {quiz_count}: {quiz_url}")
        print(f"{'='*70}\n")
        
        next_url = process_single_quiz(data, quiz_url)
        
        if next_url:
            print(f"\n[process_request] ✓ Got next quiz URL: {next_url}")
            quiz_url = next_url
        else:
            print(f"\n[process_request] ✓ Quiz chain completed!")
            break
    
    if quiz_count >= max_quizzes:
        print(f"[process_request] ⚠ Reached max quiz limit ({max_quizzes})")
    
    print(f"\n[process_request] Finished processing {quiz_count} quiz(s) for: {data.get('email')}")


def process_single_quiz(data: dict, quiz_url: str) -> str | None:
    """
    Process a single quiz and return the next URL if any.
    Returns None if no next URL (quiz chain ended).
    """
    # 1) Scrape the quiz page
    try:
        quiz_data = scrape_quiz_page(quiz_url)
    except Exception as e:
        print(f"[process_single_quiz] Error scraping quiz page: {e}")
        return None

    quiz_text  = quiz_data["quiz_text"]
    submit_url = quiz_data["submit_url"]
    file_urls  = quiz_data["file_urls"]
    all_links  = quiz_data["all_links"]
    
    # WORKAROUND: If this is demo-audio, fetch full page to get cutoff value
    if "demo-audio" in quiz_url:
        # Check if cutoff number is missing (we have "Cutoff:" but no number)
        has_cutoff_text = re.search(r'[Cc]utoff', quiz_text)
        has_cutoff_number = re.search(r'[Cc]utoff[:\s]+([0-9]+)', quiz_text)
        
        if has_cutoff_text and not has_cutoff_number:
            try:
                print("[process_single_quiz] Demo-audio detected, cutoff value missing. Using Playwright to get JS-rendered value...")
                
                # Import Playwright here to avoid issues
                from playwright.sync_api import sync_playwright
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(quiz_url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(3000)  # Wait for JS to execute
                    
                    # Get the rendered HTML
                    full_html = page.content()
                    browser.close()
                
                print(f"[process_single_quiz] Got JS-rendered HTML, length: {len(full_html)}")
                
                # Extract cutoff value from rendered HTML
                cutoff_value = None
                
                # Pattern 1: "Cutoff: 12345" or inside span tags
                # First try: Direct number after "Cutoff:"
                match = re.search(r'[Cc]utoff[:\s]*([0-9]+)', full_html)
                if match:
                    cutoff_value = match.group(1)
                    print(f"[process_single_quiz] Found cutoff via direct pattern: {cutoff_value}")
                
                # Pattern 2: Number inside <span id="cutoff">...</span>
                if not cutoff_value:
                    match = re.search(r'<span[^>]*id=["\']cutoff["\'][^>]*>([0-9]+)</span>', full_html)
                    if match:
                        cutoff_value = match.group(1)
                        print(f"[process_single_quiz] Found cutoff inside span tag: {cutoff_value}")
                
                # Pattern 3: Look for any number within 100 chars after "Cutoff"
                if not cutoff_value:
                    match = re.search(r'[Cc]utoff.{0,100}?(\d{4,6})', full_html)
                    if match:
                        cutoff_value = match.group(1)
                        print(f"[process_single_quiz] Found cutoff via proximity search: {cutoff_value}")
                
                if cutoff_value:
                    # Replace "Cutoff:" with "Cutoff: NUMBER" and add instruction about >= vs <
                    quiz_text = re.sub(r'([Cc]utoff):\s*', r'\1: ' + cutoff_value + '\nIMPORTANT: Sum numbers GREATER THAN OR EQUAL TO the cutoff (>=)\n', quiz_text)
                    print(f"[process_single_quiz] ✓ Updated quiz text with cutoff: {cutoff_value}")
                    print(f"[process_single_quiz] New quiz text (first 250 chars): {quiz_text[:250]}")
                else:
                    print(f"[process_single_quiz] ✗ Could not extract cutoff value from rendered HTML")
                    print(f"[process_single_quiz] HTML preview: {full_html[:500]}")
                    
            except Exception as e:
                print(f"[process_single_quiz] ⚠ Error in workaround: {e}")
                import traceback
                traceback.print_exc()

    print("[process_single_quiz] Scraper summary:")
    print("  source      :", quiz_data.get("source"))
    print("  submit_url  :", submit_url)
    print("  file_urls   :", file_urls)
    print("  total links :", len(all_links))

    # 2) Build enhanced prompt that teaches LLM about data_tools
    prompt_for_llm = f"""
You are an expert Python programmer that writes COMPLETE, STANDALONE scripts
to solve data-related quiz questions.

You are given:

1) Original request data (from the grading server):
{json.dumps(data, indent=2)}

2) Quiz text extracted from the quiz page:
\"\"\"{quiz_text}\"\"\"

3) Candidate submit URL (may be None if we couldn't detect it):
{submit_url!r}

4) File URLs detected on the page:
{json.dumps(file_urls, indent=2)}

5) All links detected on the page (IMPORTANT - use these when quiz mentions scraping URLs):
{json.dumps(all_links, indent=2)}

The runtime environment already has a helper module called data_tools.py.
You MAY and SHOULD use these functions instead of writing everything from scratch:

from data_tools import (
    read_csv_from_url,   # returns list[dict] from a CSV URL
    read_json_from_url,  # returns parsed JSON from a URL
    read_pdf_from_url,   # returns full text extracted from a PDF URL
    clean_text_block,    # basic normalization + lowercase
    download_text,       # download text from URL
    download_bytes,      # download binary data from URL
    fetch_js_rendered_page,  # fetch JavaScript-rendered pages (uses Playwright)
)

Allowed imports ONLY:
- standard library (re, json, io, csv, collections, math, statistics, datetime, etc.)
- httpx (for HTTP requests)
- data_tools (and functions from it)
- pypdf (only if you really need direct PDF access beyond read_pdf_from_url)
- playwright.sync_api (only via fetch_js_rendered_page from data_tools)

DO NOT import any other external libraries such as pandas, numpy, requests, matplotlib, seaborn, etc.

Your job is to write a Python script that, when RUN AS `python generated_script.py`, will:

**CRITICAL: Your script should ONLY compute the answer, NOT submit it.**

At the very end, print exactly one line in this format:
```
FINAL_ANSWER: your_computed_answer_here
```

Do NOT make any HTTP POST requests. Do NOT submit to any URL.
Just compute the answer and print it in the FINAL_ANSWER format.

1. **MANDATORY: ADD PRINT STATEMENTS for debugging**
   Print when fetching URLs, print HTML lengths, print extracted values.

2. READ THE QUIZ INSTRUCTIONS CAREFULLY to understand what is being asked.
   
3. Identify the type of task:
   - Extracting a value (secret code, text, number from a page)
   - Performing a calculation (sum, average, count, etc.)
   - Processing structured data (CSV, JSON, PDF)
   - Scraping additional pages for data

4. Download or fetch any data needed to answer the quiz.

5. **CRITICAL: CSV FILES - READ THIS FIRST IF YOU SEE A CSV:**
   
   IMPORTANT: These CSVs have NO HEADERS - just numbers, one per row!
   
   **CRITICAL: CHECK THE QUIZ TEXT FOR A CUTOFF VALUE!**
   - If the quiz mentions "Cutoff: XXXXX", check if it says "greater than or equal" (>=) or "less than" (<)
   - Default behavior if not specified: sum numbers GREATER THAN OR EQUAL TO cutoff (>=)
   - If quiz explicitly says "below" or "less than", then use (<)
   - If there's no cutoff mentioned, sum ALL numbers
   
   **EXAMPLE PATTERN:**
   ```
   import re
   
   # Extract cutoff from quiz text if present
   cutoff = None
   cutoff_match = re.search(r'[Cc]utoff[:\\s]+([0-9]+)', quiz_text)
   if cutoff_match:
       cutoff = int(cutoff_match.group(1))
       print(f"Found cutoff value: {{cutoff}}")
   
   # Get CSV URL from the file_urls list provided above
   csv_url = "INSERT_ACTUAL_CSV_URL_HERE"
   
   response = httpx.get(csv_url)
   csv_text = response.text
   print(f"CSV data length: {{len(csv_text)}}")
   
   # Read ALL lines as plain text - NO csv.DictReader!
   total = 0
   for line in csv_text.strip().split('\\n'):
       if line.strip():
           number = int(line.strip())
           # Apply cutoff filter if present
           if cutoff is None or number < cutoff:
               total += number
   
   answer = total
   print(f"Computed total from CSV: {{answer}}")
   ```
   
   **WHY THIS MATTERS:**
   - csv.DictReader assumes the first row is a header and SKIPS IT
   - But these CSVs have NO headers - the first row is DATA
   - Some quizzes ask for sum of ALL numbers, others ask for numbers BELOW a cutoff
   - ALWAYS check the quiz text for "Cutoff" or similar keywords
   
   DO NOT use csv.DictReader or read_csv_from_url() for these CSVs!
   Just read the file as text and split by newlines.

6. **CRITICAL: SCRAPING ADDITIONAL URLs:**
   If the quiz mentions scraping additional pages like "scrape /some-path?email=..." 
   YOU MUST USE THE EXACT URL FROM THE "all_links" LIST ABOVE.
   
   Example: If quiz says "Scrape /demo-scrape-data?email=test@mail.com"
   Look in the all_links list for the FULL URL like:
   "https://tds-llm-analysis.s-anand.net/demo-scrape-data?email=test@mail.com"
   
   DO NOT try to construct URLs yourself - use what's in all_links!
   Choose the URL that has the email parameter if multiple exist.

7. **DETECTING JavaScript-RENDERED PAGES:**
   Many pages load content via JavaScript. If you fetch a page with httpx.get() 
   and see it contains <script> tags but very little content (< 200 chars), 
   you MUST use fetch_js_rendered_page() instead:
   
   ```
   from data_tools import fetch_js_rendered_page
   
   response = httpx.get(url)
   html = response.text
   
   if '<script' in html and len(html.strip()) < 200:
       html = fetch_js_rendered_page(url)
   ```

8. **For HTML pages - EXTRACTING SECRET CODES:**
   Print the HTML for debugging, then try multiple strategies:
   
   Strategy 1: Look for <strong> tags (often contains correct answer)
   ```
   match = re.search(r'<strong>([^<]+)</strong>', html)
   if match:
       answer = match.group(1).strip()
   ```
   
   Strategy 2: Look for "secret" or "code" keywords
   ```
   match = re.search(r'(?:secret|code)[:\\s]+([a-zA-Z0-9_-]+)', html, re.IGNORECASE)
   ```
   
   Strategy 3: Look for standalone alphanumeric codes
   ```
   matches = re.findall(r'\\b([A-Z0-9]{{5,}})\\b', html)
   ```
   
   ALWAYS print what you found for debugging.

9. Compute the correct value for the "answer" field based on the quiz requirements.

10. **FINAL STEP: Print the answer in the required format:**
   ```
   print("FINAL_ANSWER:", your_answer_value)
   ```
   
   This MUST be the last line of output. Do NOT submit via HTTP.

Your OUTPUT should be ONLY the Python script code. Do NOT wrap it in backticks,
do NOT add explanations. Just valid Python code that ends with:
print("FINAL_ANSWER:", answer)
"""

    # 3) Call LLM to generate the script
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
                "model": "openai/gpt-4o-mini",  # Can also use: "google/gemini-2.0-flash-001" or "amazon/nova-micro"
                "max_tokens": 3000,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert Python programmer. Generate ONLY Python code, no explanations.",
                    },
                    {"role": "user", "content": prompt_for_llm},
                ],
            },
            timeout=60,
        )
        llm_response.raise_for_status()
        answer_script = llm_response.json()
    except Exception as e:
        print(f"[process_single_quiz] Error calling LLM API: {e}")
        return None

    # 4) Save the generated script and run it
    try:
        script_code = answer_script["choices"][0]["message"]["content"]
        
        # Clean up code if it's wrapped in markdown
        if script_code.startswith("```python"):
            script_code = script_code.replace("```python", "").replace("```", "").strip()
        elif script_code.startswith("```"):
            script_code = script_code.replace("```", "").strip()
        
        with open("generated_script.py", "w", encoding="utf-8") as f:
            f.write(script_code)
        
        print("[process_single_quiz] Generated script saved, executing...")
        
        complete_process = subprocess.run(
            [sys.executable, "generated_script.py"],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=120,
        )

        stdout = complete_process.stdout
        stderr = complete_process.stderr

        print("===== generated_script.py stdout =====")
        print(stdout)
        print("===== generated_script.py stderr =====")
        print(stderr)
        print("===== Return code:", complete_process.returncode, "=====")
        
        # Extract FINAL_ANSWER from stdout
        answer_value = None
        for line in stdout.splitlines():
            if line.startswith("FINAL_ANSWER:"):
                answer_value = line.split("FINAL_ANSWER:", 1)[1].strip()
                print(f"\n[process_single_quiz] ✓ Extracted answer: {answer_value}\n")
                break
        
        if not answer_value:
            print("[process_single_quiz] ✗ ERROR: Could not find FINAL_ANSWER in script output")
            return None
        
        # Build payload and submit
        if not submit_url:
            print("[process_single_quiz] ✗ ERROR: No submit_url detected")
            return None
        
        payload = {
            "email": data.get("email"),
            "secret": data.get("secret"),
            "url": quiz_url,
            "answer": answer_value,
        }
        
        print(f"[process_single_quiz] Submitting answer to: {submit_url}")
        print(f"[process_single_quiz] Payload: {payload}")
        
        try:
            resp = httpx.post(submit_url, json=payload, timeout=60.0)
            print(f"[process_single_quiz] ✓ Submission response: {resp.status_code} {resp.text}")
            
            # Try to extract next URL from response
            next_url = None
            try:
                response_data = resp.json()
                if "url" in response_data and response_data["url"]:
                    next_url = response_data["url"]
                    print(f"[process_single_quiz] ✓ Found next URL: {next_url}")
            except:
                pass
            
            return next_url
            
        except Exception as e:
            print(f"[process_single_quiz] ✗ Error submitting answer: {e}")
            return None
        
    except subprocess.TimeoutExpired:
        print("[process_single_quiz] Script execution timed out")
        return None
    except Exception as e:
        print(f"[process_single_quiz] Error executing script: {e}")
        return None


@app.post("/receive_request")
async def receive_request(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if data.get("secret") != SECRET_KEY:
        return JSONResponse(
            status_code=403, 
            content={"message": "Forbidden: Invalid secret"}
        )
    else:
        background_tasks.add_task(process_request, data)
        return JSONResponse(
            status_code=200, 
            content={"message": "Request received successfully", "data": data}
        )


if __name__ == "__main__":
    import uvicorn
    print("Starting quiz automation server on http://0.0.0.0:8000")
    print("Endpoint: POST http://0.0.0.0:8000/receive_request")
    uvicorn.run(app, host="0.0.0.0", port=8000)