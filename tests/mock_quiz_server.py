# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn[standard]"
# ]
# ///

"""
FIXED: Mock quiz server with absolute URL returns
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# Server base URL (will be set at runtime)
BASE_URL = "http://localhost:8000"

submissions = []

# ============================================================================
# QUIZ 1: CSV ANALYSIS
# ============================================================================

@app.get("/quiz-csv", response_class=HTMLResponse)
async def quiz_csv():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>CSV Analysis Quiz</title></head>
    <body>
        <h1>CSV Data Analysis</h1>
        <div id="content">
            <p>Download the <a href="/data/numbers.csv">CSV file</a>.</p>
            <p>Cutoff: 500</p>
            <p><strong>Task:</strong> Calculate the sum of all numbers that are greater than or equal to the cutoff value.</p>
            <p>Submit your answer to <code>/submit</code></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/data/numbers.csv")
async def serve_csv():
    """NO HEADERS - just numbers. Sum of numbers >= 500 = 3150"""
    csv_content = "250\n350\n500\n650\n750\n850\n100\n50"
    return PlainTextResponse(csv_content, media_type="text/csv")


# ============================================================================
# QUIZ 2: API DATA
# ============================================================================

@app.get("/quiz-api", response_class=HTMLResponse)
async def quiz_api():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>API Data Quiz</title></head>
    <body>
        <h1>API Data Analysis</h1>
        <div id="content">
            <p>Fetch data from: <code>GET /api/sales</code></p>
            <p><strong>Task:</strong> Calculate total revenue for products where status is "active".</p>
            <p>Submit to <code>/submit</code></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/api/sales")
async def api_sales():
    """Total revenue for active = 4500"""
    return {
        "products": [
            {"name": "Widget A", "status": "active", "revenue": 1000},
            {"name": "Widget B", "status": "inactive", "revenue": 500},
            {"name": "Widget C", "status": "active", "revenue": 1500},
            {"name": "Widget D", "status": "active", "revenue": 2000},
            {"name": "Widget E", "status": "inactive", "revenue": 800},
        ]
    }


# ============================================================================
# QUIZ 3: WEB SCRAPING
# ============================================================================

@app.get("/quiz-scrape", response_class=HTMLResponse)
async def quiz_scrape():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Scraping Quiz</title></head>
    <body>
        <h1>Web Scraping Challenge</h1>
        <div id="content">
            <p>Visit <code>/secret-page</code> and extract the secret code.</p>
            <p>It's in a <code>&lt;strong&gt;</code> tag.</p>
            <p>Submit to <code>/submit</code></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/secret-page", response_class=HTMLResponse)
async def secret_page():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Secret Page</title></head>
    <body>
        <h1>Find the Secret</h1>
        <p>The secret code is: <strong>ALPHA123BETA</strong></p>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================================================
# QUIZ 4: VISUALIZATION
# ============================================================================

@app.get("/quiz-viz", response_class=HTMLResponse)
async def quiz_viz():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Visualization Quiz</title></head>
    <body>
        <h1>Data Visualization</h1>
        <div id="content">
            <p>Download <a href="/data/categories.csv">CSV file</a>.</p>
            <p><strong>Task:</strong> Create a BAR CHART showing values for each category.</p>
            <p>Return as base64 PNG data URI.</p>
            <p>Submit to <code>/submit</code></p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/data/categories.csv")
async def serve_categories():
    """CSV WITH HEADERS"""
    csv_content = """category,value
A,120
B,85
C,150
D,95
E,110"""
    return PlainTextResponse(csv_content, media_type="text/csv")


# ============================================================================
# QUIZ 5: MULTI-STEP
# ============================================================================

@app.get("/quiz-chain-1", response_class=HTMLResponse)
async def quiz_chain_1():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Multi-Step Quiz - Part 1</title></head>
    <body>
        <h1>Multi-Step Quiz - Part 1</h1>
        <div><p><strong>Task:</strong> What is 10 + 20?</p><p>Submit to <code>/submit</code></p></div>
    </body>
    </html>
    """
    return HTMLResponse(html)


@app.get("/quiz-chain-2", response_class=HTMLResponse)
async def quiz_chain_2():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Multi-Step Quiz - Part 2</title></head>
    <body>
        <h1>Multi-Step Quiz - Part 2</h1>
        <div><p><strong>Task:</strong> What is 50 * 2?</p><p>Submit to <code>/submit</code></p></div>
    </body>
    </html>
    """
    return HTMLResponse(html)


# ============================================================================
# SUBMISSION ENDPOINT (FIXED - Returns absolute URLs)
# ============================================================================

@app.post("/submit")
async def submit_answer(request: Request):
    """FIXED: Returns absolute URLs"""
    data = await request.json()
    print(f"\n📥 Submission: {data.get('url')} → {data.get('answer')}")
    submissions.append(data)
    
    quiz_url = data.get("url", "")
    answer = data.get("answer")
    
    # CSV Quiz
    if "quiz-csv" in quiz_url:
        correct = answer == 2750 or answer == "2750"
        return {
            "correct": correct,
            "message": "Correct! Sum >= 500 is 2750" if correct else f"Wrong. Expected 2750, got {answer}",
            "url": f"{BASE_URL}/quiz-api" if correct else f"{BASE_URL}/quiz-api"
        }
    
    # API Quiz
    elif "quiz-api" in quiz_url:
        correct = answer == 4500 or answer == "4500"
        return {
            "correct": correct,
            "message": "Correct! Revenue = 4500" if correct else f"Wrong. Expected 4500, got {answer}",
            "url": f"{BASE_URL}/quiz-scrape" if correct else f"{BASE_URL}/quiz-scrape"
        }
    
    # Scraping Quiz
    elif "quiz-scrape" in quiz_url:
        correct = str(answer).strip() == "ALPHA123BETA"
        return {
            "correct": correct,
            "message": "Correct! Found secret code" if correct else f"Wrong. Expected ALPHA123BETA, got {answer}",
            "url": f"{BASE_URL}/quiz-viz" if correct else f"{BASE_URL}/quiz-viz"
        }
    
    # Visualization Quiz
    elif "quiz-viz" in quiz_url:
        is_base64 = isinstance(answer, str) and answer.startswith("data:image/png;base64,")
        return {
            "correct": is_base64,
            "message": "Correct! Valid chart" if is_base64 else "Must be base64 PNG data URI",
            "url": None
        }
    
    # Chain Quiz 1
    elif "quiz-chain-1" in quiz_url:
        correct = answer == 30 or answer == "30"
        return {
            "correct": correct,
            "message": "Correct! 10 + 20 = 30" if correct else f"Wrong. Expected 30",
            "url": f"{BASE_URL}/quiz-chain-2" if correct else f"{BASE_URL}/quiz-chain-2"
        }
    
    # Chain Quiz 2
    elif "quiz-chain-2" in quiz_url:
        correct = answer == 100 or answer == "100"
        return {
            "correct": correct,
            "message": "Correct! 50 * 2 = 100" if correct else f"Wrong. Expected 100",
            "url": None
        }
    
    return {"correct": False, "message": "Unknown quiz", "url": None}


@app.get("/submissions")
async def view_submissions():
    return {"submissions": submissions, "count": len(submissions)}


@app.get("/reset")
async def reset_submissions():
    global submissions
    submissions = []
    return {"message": "Submissions reset"}


@app.get("/")
async def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock Quiz Server</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
            .quiz-list { list-style: none; padding: 0; }
            .quiz-list li { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
            a { color: #0066cc; text-decoration: none; }
        </style>
    </head>
    <body>
        <h1>🎯 Mock Quiz Server - FIXED VERSION</h1>
        <h2>Available Quizzes:</h2>
        <ul class="quiz-list">
            <li><strong>CSV:</strong> <a href="/quiz-csv">/quiz-csv</a> (sum >= 500 = 3150)</li>
            <li><strong>API:</strong> <a href="/quiz-api">/quiz-api</a> (active revenue = 4500)</li>
            <li><strong>Scraping:</strong> <a href="/quiz-scrape">/quiz-scrape</a> (code = ALPHA123BETA)</li>
            <li><strong>Visualization:</strong> <a href="/quiz-viz">/quiz-viz</a> (bar chart)</li>
            <li><strong>Chain:</strong> <a href="/quiz-chain-1">/quiz-chain-1</a> (30 → 100)</li>
        </ul>
        <p><a href="/submissions">View Submissions</a> | <a href="/reset">Reset</a></p>
    </body>
    </html>
    """
    return HTMLResponse(html)


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FIXED mock quiz server...")
    print("📍 Server: http://localhost:8000")
    print("✅ Returns absolute URLs for chaining")
    print("✅ Fixed answer expectations")
    uvicorn.run(app, host="0.0.0.0", port=8000)