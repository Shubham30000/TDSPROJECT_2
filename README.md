# 🤖 Automated LLM Quiz Solver

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace-orange.svg)](https://zenitsu2121-tds-quiz-solver.hf.space/)

An intelligent system that autonomously solves data analysis quizzes using Large Language Models (LLMs) and web scraping technologies. Built for the IIT Madras TDS Course Project 2.

## 🎯 Project Overview

This project implements an end-to-end automated quiz-solving pipeline that:
- ✅ Receives quiz URLs via REST API with proper validation (HTTP 400/403 handling)
- ✅ Scrapes quiz instructions from JavaScript-rendered web pages
- ✅ Analyzes requirements and generates Python scripts dynamically using LLMs
- ✅ Executes scripts to compute answers from various data sources (CSV, JSON, PDF, APIs)
- ✅ **Implements retry logic** - retries wrong answers up to 3 times within 3-minute timeout
- ✅ Submits answers and handles multi-stage quiz chains automatically
- ✅ **Supports data visualization** - generates charts as base64 PNG images

**Live Demo:** [https://zenitsu2121-tds-project2.hf.space](https://zenitsu2121-tds-quiz-solver.hf.space/)

---

## ✨ Key Features

### 🌐 Advanced Web Scraping
- **Static HTML parsing** using BeautifulSoup
- **JavaScript-rendered pages** with Playwright (headless Chromium)
- Automatic detection and switching between scraping strategies
- Robust text extraction with multiple fallback methods

### 📊 Multi-Format Data Processing
- ✅ **CSV files** (headerless and standard formats)
- ✅ **JSON data** from REST APIs
- ✅ **PDF document** text extraction
- ✅ **Data visualization** (bar charts, line charts, pie charts)
- ✅ Dynamic cutoff-based filtering and aggregations

### 🧠 LLM-Powered Script Generation
- Generates complete Python scripts from natural language quiz instructions
- Provides comprehensive error handling and debugging output
- Adapts to different question types automatically
- Uses **GPT-4o-mini** via OpenRouter API

### 🔄 Automated Quiz Chain Handling
- ✅ **Retry Logic**: Retries wrong answers up to 3 times per quiz
- ✅ **3-Minute Timeout**: Respects overall time limit per request
- ✅ Processes sequential quizzes without manual intervention (up to 10 quizzes)
- ✅ Handles both correct and incorrect answer scenarios
- ✅ Logs detailed execution traces for debugging

### 🛡️ Robust Error Handling
- ✅ **HTTP 400**: Returns proper error for invalid JSON payloads
- ✅ **HTTP 403**: Returns proper error for invalid secret keys
- ✅ **HTTP 200**: Accepts valid requests and processes in background
- ✅ Graceful degradation on failures

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Quiz Server   │ ──POST──> {email, secret, url}
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      FastAPI Endpoint (app.py)          │
│    POST /receive_request                │
│  • HTTP 400 for invalid JSON            │
│  • HTTP 403 for invalid secret          │
│  • HTTP 200 + background processing     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Background Task Processor              │
│  • 3-minute overall timeout             │
│  • Up to 10 sequential quizzes          │
│  • Retry logic (3 attempts per quiz)    │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     Web Scraper (scraper.py)            │
│  • Playwright (JS-rendered pages)       │
│  • BeautifulSoup (Static HTML)          │
│  • Extracts quiz text & file URLs       │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│    LLM Script Generator                 │
│  • Analyzes quiz requirements           │
│  • Generates Python solving script      │
│  • Includes data_tools imports          │
│  • Template-based approach              │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   Script Executor (subprocess)          │
│  • Runs generated script                │
│  • Captures stdout/stderr               │
│  • Extracts FINAL_ANSWER                │
│  • 120-second timeout per execution     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│    Answer Submission                    │
│  • POSTs to quiz submit endpoint        │
│  • Checks if answer is correct          │
│  • Retries if wrong (max 3 attempts)    │
│  • Handles next URL in chain            │
│  • Loops until quiz completion          │
└─────────────────────────────────────────┘
```

---

## 🚀 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI (async REST API) |
| **Web Scraping** | Playwright (browser automation), BeautifulSoup4 (HTML parsing) |
| **LLM Integration** | OpenRouter API (GPT-4o-mini) |
| **Data Processing** | httpx, pypdf, csv, json, matplotlib |
| **Visualization** | matplotlib (charts as base64 PNG) |
| **Deployment** | Docker, HuggingFace Spaces |
| **Language** | Python 3.11 |

---

## 📁 Project Structure

```
TDSPROJECT_2/
├── app.py                    # FastAPI server with /receive_request endpoint
│                             # ✅ HTTP 400/403 handling
│                             # ✅ Retry logic (3 attempts)
│                             # ✅ 3-minute timeout
│
├── scraper.py                # Web scraping logic (static + JS-rendered)
│
├── data_tools.py             # Helper functions for data processing
│                             # ✅ CSV/JSON/PDF parsing
│                             # ✅ Visualization (bar/line/pie charts)
│                             # ✅ Base64 image encoding
│
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker container configuration
├── README.md                 # This file
├── LICENSE                   # MIT License
└── .gitignore                # Git ignore rules
```

---

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- Git
- (Optional) Docker for containerized deployment

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Shubham30000/TDSPROJECT_2.git
cd TDSPROJECT_2

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Create .env file with your credentials
cat > .env << EOF
AIPIPE_TOKEN=your_aipipe_token_here
AIPIPE_API_URL=https://aipipe.org/openrouter/v1/chat/completions
SECRET_KEY=your_secret_key_here
EOF

# 6. Run the server
python app.py
```

The server will start at `http://localhost:7860`

### Docker Deployment

```bash
# Build image
docker build -t llm-quiz-solver .

# Run container
docker run -p 7860:7860 \
  -e AIPIPE_TOKEN_SECRET=your_token \
  -e AIPIPE_API_URL_SECRET=your_api_url \
  -e SECRET_KEY_SECRET=your_secret \
  llm-quiz-solver
```

---

## 📡 API Usage

### Endpoint: `POST /receive_request`

#### Request Body
```json
{
  "email": "student@example.com",
  "secret": "your_secret_key",
  "url": "https://quiz-server.com/quiz-123"
}
```

#### Response Codes

| Code | Meaning | Response |
|------|---------|----------|
| **200** | Success | `{"message": "Request received successfully", "data": {...}}` |
| **400** | Bad Request | `{"message": "Bad Request: Invalid JSON payload"}` |
| **403** | Forbidden | `{"message": "Forbidden: Invalid secret"}` |

#### Example: Testing with cURL

```bash
# Valid request
curl -X POST http://localhost:7860/receive_request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@mail.com",
    "secret": "your_secret_key",
    "url": "https://quiz-server.com/quiz-123"
  }'

# Invalid JSON (returns HTTP 400)
curl -X POST http://localhost:7860/receive_request \
  -H "Content-Type: application/json" \
  -d 'invalid json here'

# Invalid secret (returns HTTP 403)
curl -X POST http://localhost:7860/receive_request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@mail.com",
    "secret": "wrong_secret",
    "url": "https://quiz-server.com/quiz-123"
  }'
```

---

## 🧪 How It Works

### 1. **Quiz Reception**
The FastAPI endpoint receives a POST request with quiz URL and validates:
- ✅ JSON payload format (returns HTTP 400 if invalid)
- ✅ Secret key (returns HTTP 403 if wrong)
- ✅ Accepts request and processes in background (HTTP 200)

### 2. **Web Scraping**
- First attempts static HTML scraping with `httpx`
- If content is minimal (< 200 chars), switches to Playwright for JS-rendered pages
- Extracts quiz instructions, submit URLs, and file URLs using regex patterns

### 3. **LLM Script Generation**
Sends a detailed prompt to GPT-4o-mini containing:
- Original request data
- Scraped quiz text
- Available helper functions from `data_tools.py`
- Code templates for common patterns
- Instructions to output a standalone Python script

### 4. **Script Execution**
- Saves generated script as `generated_script.py`
- Executes with subprocess (120s timeout)
- Captures output and extracts `FINAL_ANSWER: <value>`

### 5. **Answer Submission with Retry Logic**
- POSTs answer to the submit URL specified in quiz
- **If correct**: Proceeds to next quiz URL (if provided)
- **If wrong**: Retries up to 3 times (or skips to next URL if provided by server)
- **3-minute overall timeout**: Ensures request completes within time limit
- Repeats process for up to 10 quizzes in a chain

---

## 📊 Supported Quiz Types

| Quiz Type | Description | Status |
|-----------|-------------|--------|
| **CSV Analysis** | Sum/filter/aggregate data from CSV files | ✅ Supported |
| **JSON APIs** | Parse REST API responses | ✅ Supported |
| **Web Scraping** | Extract secret codes from HTML pages | ✅ Supported |
| **PDF Processing** | Extract text from PDF documents | ✅ Supported |
| **Data Visualization** | Generate charts (bar/line/pie) as base64 PNG | ✅ Supported |
| **Multi-Step Chains** | Sequential quizzes with dependencies | ✅ Supported |
| **Simple Math** | Basic arithmetic calculations | ✅ Supported |

---

## 🎓 Technical Highlights

### ✅ **Complete Requirements Implementation**

1. **HTTP Error Handling** ✓
   - HTTP 400 for invalid JSON payloads
   - HTTP 403 for invalid secret keys
   - HTTP 200 for valid requests with background processing

2. **Retry Logic** ✓
   - Up to 3 attempts per quiz
   - Respects 3-minute overall timeout
   - Handles both retry-on-fail and skip-to-next scenarios

3. **Quiz Chain Support** ✓
   - Processes up to 10 sequential quizzes
   - Automatic next-URL detection and following
   - Comprehensive logging for debugging

4. **Data Visualization** ✓
   - Bar charts, line charts, pie charts
   - Returns as base64 PNG data URIs
   - Uses matplotlib with non-interactive backend

### 🏆 **Engineering Best Practices**

- **Clean Architecture**: Modular design with separated concerns
- **Async Processing**: Non-blocking background tasks with FastAPI
- **Type Safety**: Python type hints throughout codebase
- **Error Handling**: Comprehensive try-catch with graceful degradation
- **Logging**: Detailed debug output for troubleshooting
- **Security**: Environment variable management, secret validation
- **Testing**: Mock server and test suite included
- **Documentation**: Clear code comments and README

---

## 🐛 Debugging & Logs

The system provides detailed logging for every step:

```python
[receive_request] ✓ Valid request from test@mail.com

PROCESSING QUIZ 1: http://localhost:8000/quiz-csv
Time remaining: 178.5s

[Attempt 1/3]
[process_single_quiz] Scraper summary:
  submit_url  : http://localhost:8000/submit
  file_urls   : ['http://localhost:8000/data/numbers.csv']
  page_urls   : []
  total links : 2

[process_single_quiz] Generated code:
======================================================================
import httpx

csv_url = "http://localhost:8000/data/numbers.csv"
text = httpx.get(csv_url).text
print(f"CSV Content: {text}")

lines = text.strip().split('\n')
numbers = [int(line.strip()) for line in lines if line.strip()]
print(f"Parsed numbers: {numbers}")

cutoff = 500
result = sum(n for n in numbers if n >= cutoff)

print(f"FINAL_ANSWER: {result}")
======================================================================

===== EXECUTION OUTPUT =====
CSV Content: 250
350
500
650
750
850
100
50

Parsed numbers: [250, 350, 500, 650, 750, 850, 100, 50]
FINAL_ANSWER: 2750
===== Exit code: 0 =====

✓ Extracted answer: 2750

📤 Submitting to: http://localhost:8000/submit
📋 Payload: {
  "email": "test@mail.com",
  "secret": "your_secret",
  "url": "http://localhost:8000/quiz-csv",
  "answer": 2750
}

📥 Server response [200]: {"correct":true,"message":"Correct!","url":"http://localhost:8000/quiz-api"}
✅ CORRECT! Correct! Sum >= 500 is 2750

[process_request] ✓ Got next quiz URL: http://localhost:8000/quiz-api
```

---

## 📦 Dependencies

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
playwright==1.40.0
beautifulsoup4==4.12.2
lxml==4.9.3
pypdf==3.17.4
python-dotenv==1.0.0
matplotlib==3.8.2
pillow==10.1.0
```

---

## 🚧 Testing

### Run Mock Quiz Server

```bash
# Terminal 1 - Start mock quiz server
python mock_quiz_server_complete.py
```

### Run Main Application

```bash
# Terminal 2 - Start main app
python app.py
```

### Run Tests

```bash
# Terminal 3 - Run comprehensive tests
python test_system_improved.py
```

**Expected Output:**
```
🚀 COMPREHENSIVE QUIZ SOLVER TESTS - IMPROVED
======================================================================

✅ Main server: http://localhost:7860
✅ Mock server: http://localhost:8000
✅ Reset complete

======================================================================
🧪 TESTING: CSV Analysis
======================================================================
✅ PASS: Match: 2750

======================================================================
🧪 TESTING: API Data
======================================================================
✅ PASS: Match: 4500

======================================================================
🧪 TESTING: Web Scraping
======================================================================
✅ PASS: Match: ALPHA123BETA

======================================================================
🧪 TESTING: Visualization
======================================================================
✅ PASS: Custom validation passed

======================================================================
🧪 TESTING: Multi-Step Chain
======================================================================
✅ PASS: Custom validation passed

======================================================================
📊 FINAL RESULTS
======================================================================
✓ Passed: 5/5
  ✅ CSV Analysis
  ✅ API Data
  ✅ Web Scraping
  ✅ Visualization
  ✅ Multi-Step Chain

🎉 ALL TESTS PASSED!
✨ System working perfectly!
```

---

## 📝 Project Requirements Coverage

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| HTTP 400 for invalid JSON | ✅ | `app.py:304-312` |
| HTTP 403 for invalid secret | ✅ | `app.py:315-320` |
| HTTP 200 for valid requests | ✅ | `app.py:323-330` |
| Retry logic (wrong answers) | ✅ | `app.py:49-295` (3 attempts) |
| 3-minute timeout | ✅ | `app.py:37-43` |
| Quiz chain handling | ✅ | `app.py:32-59` (up to 10) |
| CSV processing | ✅ | `data_tools.py:30-40` |
| JSON API handling | ✅ | `data_tools.py:43-50` |
| PDF text extraction | ✅ | `data_tools.py:53-69` |
| Web scraping | ✅ | `scraper.py` |
| Data visualization | ✅ | `data_tools.py:92-185` |
| Background processing | ✅ | FastAPI BackgroundTasks |
| LLM integration | ✅ | OpenRouter GPT-4o-mini |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Shubham**
- GitHub: [@Shubham30000](https://github.com/Shubham30000)
- Project Repository: [TDSPROJECT_2](https://github.com/Shubham30000/TDSPROJECT_2)
- Live Demo: [HuggingFace Space](https://huggingface.co/spaces/Zenitsu2121/TDS_Project2)

---

## 🙏 Acknowledgments

- **IIT Madras TDS Course** for the project specifications
- **OpenRouter/AIPipe** for LLM API access
- **HuggingFace** for free hosting infrastructure
- **FastAPI & Playwright** communities for excellent documentation

---

## 📞 Contact

For questions, feedback, or collaboration opportunities:
- 📧 Open an issue on GitHub
- 🌟 Star this repository if you find it useful
- 🔗 Share with others working on similar projects

---

<div align="center">

**Built with ❤️ for learning and innovation**

⭐ **If you find this project useful, please consider giving it a star!** ⭐

</div>
