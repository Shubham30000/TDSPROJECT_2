# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn[standard]"
# ]
# ///

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

app = FastAPI()

# ===================== STEP 1: API + CSV =====================

@app.get("/api/data-step1")
async def api_data_step1():
    # Simple JSON for step 1
    return {
        "items": [
            {"id": 1, "category": "A", "value": 10},
            {"id": 2, "category": "B", "value": 20},
            {"id": 3, "category": "A", "value": 30},
            {"id": 4, "category": "B", "value": 40},
        ]
    }

@app.get("/files/fees-step1.csv")
async def fees_step1():
    csv_content = "category,fee\nA,5\nB,7\n"
    return PlainTextResponse(csv_content, media_type="text/csv")

@app.get("/quiz-1", response_class=HTMLResponse)
async def quiz_1():
    html = """
    <html>
      <body>
        <h1>Multi-step Quiz - Step 1</h1>
        <pre>
Q1. Use this API endpoint:

  GET http://localhost:9001/api/data-step1

It returns JSON like:
  {
    "items": [
      {"id": 1, "category": "A", "value": 10},
      {"id": 2, "category": "B", "value": 20},
      ...
    ]
  }

Also download the CSV file:

  http://localhost:9001/files/fees-step1.csv

It contains:
  category,fee
  A,5
  B,7

TASK:
  1. Compute total_value_by_category from the JSON:
       sum of "value" for each category A and B.
     - Category A: 10 + 30 = 40
     - Category B: 20 + 40 = 60

  2. From CSV, get fee per category:
     - A -> 5
     - B -> 7

  3. Compute final_score as:
       final_score = (total_A * fee_A) + (total_B * fee_B)
                   = (40 * 5) + (60 * 7)
                   = 200 + 420 = 620

SUBMIT:
  POST your answer JSON to:

    http://localhost:9001/submit-step1

  with this JSON payload:

  {
    "email": "your email",
    "secret": "your secret",
    "url": "http://localhost:9001/quiz-1",
    "answer": 620
  }

If correct, the response JSON will include a new "url" for quiz-2.
        </pre>
      </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/submit-step1")
async def submit_step1(req: Request):
    data = await req.json()
    answer = data.get("answer")

    if answer == 620:
        return JSONResponse({
            "correct": True,
            "reason": "",
            "url": "http://localhost:9001/quiz-2"
        })
    else:
        return JSONResponse({
            "correct": False,
            "reason": f"Expected 620 but got {answer}",
            "url": "http://localhost:9001/quiz-2"
        })

# ===================== STEP 2: API only =====================

@app.get("/api/data-step2")
async def api_data_step2():
    return {
        "measurements": [5, 7, 9, 11, 13]  # mean = 9
    }

@app.get("/quiz-2", response_class=HTMLResponse)
async def quiz_2():
    html = """
    <html>
      <body>
        <h1>Multi-step Quiz - Step 2 (Final)</h1>
        <pre>
Q2. Use this API endpoint:

  GET http://localhost:9001/api/data-step2

It returns JSON:
  {
    "measurements": [5, 7, 9, 11, 13]
  }

TASK:
  Compute the arithmetic mean (average) of "measurements":
    (5 + 7 + 9 + 11 + 13) / 5 = 45 / 5 = 9

SUBMIT:
  POST your answer JSON to:

    http://localhost:9001/submit-step2

  with this JSON payload:

  {
    "email": "your email",
    "secret": "your secret",
    "url": "http://localhost:9001/quiz-2",
    "answer": 9
  }

If correct, there will be NO new "url" field, indicating the quiz is over.
        </pre>
      </body>
    </html>
    """
    return HTMLResponse(html)

@app.post("/submit-step2")
async def submit_step2(req: Request):
    data = await req.json()
    answer = data.get("answer")

    if answer == 9:
        return JSONResponse({
            "correct": True,
            "reason": "",
            "url": None
        })
    else:
        return JSONResponse({
            "correct": False,
            "reason": f"Expected 9 but got {answer}",
            "url": None
        })

# ===================== ENTRYPOINT =====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mock_quiz_server:app", host="0.0.0.0", port=9001)
