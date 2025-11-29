# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "fastapi",
#   "uvicorn[standard]",
#   "httpx"
# ]
# ///

"""
Simple mock quiz server that serves CSV data for testing.
No PDF dependencies required!
"""

from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

# Track submissions
submissions = []


@app.get("/", response_class=HTMLResponse)
async def quiz_page():
    """
    Quiz page that references a CSV file.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSV Data Analysis Quiz</title>
    </head>
    <body>
        <h1>Sales Data Analysis Quiz</h1>
        <p>
            Download the CSV file below and calculate the total sales amount 
            for all products where status is "active".
        </p>
        <p>
            <a href="/data.csv">Download Sales CSV</a>
        </p>
        <form action="/submit" method="POST">
            <input type="text" name="answer" placeholder="Your answer" />
            <button type="submit">Submit</button>
        </form>
        <hr>
        <p><em>Hint: Expected answer is 1250</em></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/data.csv")
async def serve_csv():
    """
    Serve a test CSV file.
    """
    csv_content = """product,status,sales
Widget A,active,500
Widget B,inactive,200
Widget C,active,300
Widget D,active,450
Widget E,inactive,100
"""
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=data.csv"}
    )


@app.post("/submit")
async def submit_answer(request: dict):
    """
    Accept quiz submissions.
    """
    print(f"Received submission: {request}")
    submissions.append(request)
    
    answer = request.get("answer")
    
    # Check if answer is correct (should be 1250)
    if answer == 1250 or answer == "1250":
        return {
            "status": "success",
            "message": "Correct! The total sales for active products is 1250.",
            "correct": True
        }
    else:
        return {
            "status": "incorrect",
            "message": f"Wrong answer. You submitted: {answer}",
            "correct": False,
            "hint": "Sum sales where status='active': 500 + 300 + 450 = 1250"
        }


@app.get("/submissions")
async def view_submissions():
    """
    View all submissions (for debugging).
    """
    return {"submissions": submissions}


if __name__ == "__main__":
    import uvicorn
    print("Starting simple mock quiz server on http://localhost:8001")
    print("Quiz page: http://localhost:8001/")
    print("CSV file: http://localhost:8001/data.csv")
    print("Submit endpoint: POST http://localhost:8001/submit")
    uvicorn.run(app, host="0.0.0.0", port=8001)