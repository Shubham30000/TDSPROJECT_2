# 🤖 Automated LLM Quiz Solver

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HuggingFace](https://img.shields.io/badge/🤗-HuggingFace-orange.svg)](https://huggingface.co/spaces/Zenitsu2121/TDS_Project2)

An intelligent system that autonomously solves data analysis quizzes using Large Language Models (LLMs) and web scraping technologies. Built for the IIT Madras TDS Course Project.

## 🎯 Project Overview

This project implements an end-to-end automated quiz-solving pipeline that:
- Receives quiz URLs via REST API
- Scrapes quiz instructions from JavaScript-rendered web pages
- Analyzes requirements and generates Python scripts dynamically using LLMs
- Executes scripts to compute answers from various data sources (CSV, JSON, PDF, APIs)
- Submits answers and handles multi-stage quiz chains automatically

**Live Demo:** [https://zenitsu2121-tds-project2.hf.space](https://zenitsu2121-tds-project2.hf.space)

## ✨ Key Features

### 🌐 Advanced Web Scraping
- **Static HTML parsing** using BeautifulSoup
- **JavaScript-rendered pages** with Playwright (headless Chromium)
- Automatic detection and switching between scraping strategies
- Robust text extraction with multiple fallback methods

### 📊 Multi-Format Data Processing
- CSV files (headerless and standard formats)
- JSON data from REST APIs
- PDF document text extraction
- Dynamic cutoff-based filtering and aggregations

### 🧠 LLM-Powered Script Generation
- Generates complete Python scripts from natural language quiz instructions
- Provides comprehensive error handling and debugging output
- Adapts to different question types automatically
- Uses GPT-4o-mini via OpenRouter API

### 🔄 Automated Quiz Chain Handling
- Processes sequential quizzes without manual intervention
- Handles both correct and incorrect answer scenarios
- Respects 3-minute time limits per quiz
- Logs detailed execution traces for debugging

## 🏗️ Architecture
```
┌─────────────────┐
│   Quiz Server   │ ──POST──> {email, secret, url}
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Endpoint                │
│    (app.py - /receive_request)          │
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
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   Script Executor (subprocess)          │
│  • Runs generated script                │
│  • Captures stdout/stderr               │
│  • Extracts FINAL_ANSWER                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│    Answer Submission                    │
│  • POSTs to quiz submit endpoint        │
│  • Handles next URL in chain            │
│  • Loops until quiz completion          │
└─────────────────────────────────────────┘
```

## 🚀 Tech Stack

- **Backend Framework:** FastAPI (async REST API)
- **Web Scraping:** Playwright (browser automation), BeautifulSoup4 (HTML parsing)
- **LLM Integration:** OpenRouter API (GPT-4o-mini)
- **Data Processing:** httpx, pypdf, csv, json
- **Deployment:** Docker, HuggingFace Spaces
- **Language:** Python 3.11

## 📁 Project Structure
```
TDSPROJECT_2/
├── app.py                 # FastAPI server with /receive_request endpoint
├── scraper.py            # Web scraping logic (static + JS-rendered)
├── data_tools.py         # Helper functions for CSV/JSON/PDF processing
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker container configuration
├── README.md            # This file
├── LICENSE              # MIT License
└── .gitignore          # Git ignore rules
```

## 🔧 Installation & Setup

### Local Development
```bash
# Clone the repository
git clone https://github.com/Shubham30000/TDSPROJECT_2.git
cd TDSPROJECT_2

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Create .env file with your credentials
cat > .env << EOF
AIPIPE_TOKEN=your_aipipe_token_here
AIPIPE_API_URL=https://aipipe.org/openrouter/v1/chat/completions
SECRET_KEY=your_secret_key_here
EOF

# Run the server
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

## 📡 API Usage

### Endpoint: `POST /receive_request`

**Request:**
```json
{
  "email": "student@example.com",
  "secret": "your_secret_key",
  "url": "https://quiz-server.com/quiz-123"
}
```

**Response (200 OK):**
```json
{
  "message": "Request received successfully",
  "data": {
    "email": "student@example.com",
    "secret": "your_secret_key",
    "url": "https://quiz-server.com/quiz-123"
  }
}
```

**Response (403 Forbidden):**
```json
{
  "message": "Forbidden: Invalid secret"
}
```

### Testing with Demo Endpoint
```bash
curl -X POST https://zenitsu2121-tds-project2.hf.space/receive_request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@mail.com",
    "secret": "something_random_12345",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

## 🧪 How It Works

### 1. **Quiz Reception**
The FastAPI endpoint receives a POST request with quiz URL and validates the secret key.

### 2. **Web Scraping**
- First attempts static HTML scraping with `httpx`
- If content is minimal (< 200 chars), switches to Playwright for JS-rendered pages
- Extracts quiz instructions, submit URLs, and file URLs using regex patterns

### 3. **LLM Script Generation**
Sends a detailed prompt to GPT-4o-mini containing:
- Original request data
- Scraped quiz text
- Available helper functions from `data_tools.py`
- Examples and best practices
- Instructions to output a standalone Python script

### 4. **Script Execution**
- Saves generated script as `generated_script.py`
- Executes with subprocess (120s timeout)
- Captures output and extracts `FINAL_ANSWER: <value>`

### 5. **Answer Submission**
- POSTs answer to the submit URL specified in quiz
- Parses response for `"url"` field indicating next quiz
- Repeats process for up to 10 quizzes in a chain

## 📊 Supported Quiz Types

| Quiz Type | Description | Example |
|-----------|-------------|---------|
| **Web Scraping** | Extract secret codes from HTML pages | Find hidden text in `<strong>` tags |
| **CSV Analysis** | Sum/filter/aggregate data from CSV files | Sum numbers ≥ cutoff value |
| **JSON APIs** | Parse REST API responses | Extract specific fields from JSON |
| **PDF Processing** | Extract text from PDF documents | Find values in PDF tables |
| **Data Transformation** | Filter, sort, reshape data | Group by, pivot operations |
| **Calculations** | Mathematical operations | Average, median, standard deviation |

## 🎓 Technical Highlights for Recruiters

### Problem-Solving Skills
- **Dynamic Code Generation:** Uses LLMs to generate context-specific Python scripts rather than hardcoding solutions
- **Robust Error Handling:** Multiple fallback strategies for web scraping and data extraction
- **Adaptive Processing:** Automatically detects quiz requirements and adjusts approach

### System Design
- **Asynchronous Architecture:** FastAPI with background tasks for non-blocking execution
- **Modular Design:** Separated concerns (scraping, data tools, API logic)
- **Scalable Deployment:** Dockerized for easy deployment on any platform

### Engineering Best Practices
- **Clean Code:** Well-documented functions with clear responsibilities
- **Type Safety:** Uses Python type hints throughout
- **Logging:** Comprehensive debug output for troubleshooting
- **Security:** Environment variable management, secret validation

## 🐛 Debugging & Logs

The system provides detailed logging:
```python
[process_single_quiz] Scraper summary:
  source      : playwright (no selector)
  submit_url  : https://example.com/submit
  file_urls   : ['https://example.com/data.csv']
  total links : 5

[process_single_quiz] Generated script saved, executing...
===== generated_script.py stdout =====
Cutoff value: 21217
CSV data length: 5886
Computed total from CSV: 47052081
FINAL_ANSWER: 47052081
===== Return code: 0 =====

[process_single_quiz] ✓ Extracted answer: 47052081
[process_single_quiz] ✓ Submission response: 200 {"correct":true,...}
```

## 🚧 Known Limitations

- **Visualization Tasks:** No support for generating charts/images (requires matplotlib/plotly)
- **Advanced ML:** No pandas/numpy/scikit-learn for complex statistical analysis
- **Rate Limits:** OpenRouter API has rate limits; may fail under high load
- **3-Minute Timeout:** Complex quizzes requiring extensive processing may timeout

## 🔮 Future Enhancements

- [ ] Add support for image/chart generation (matplotlib, seaborn)
- [ ] Integrate pandas for advanced data analysis
- [ ] Implement retry logic with exponential backoff
- [ ] Add caching for repeated quiz URLs
- [ ] Support for multi-model LLM fallback (GPT-4, Claude, Gemini)
- [ ] Real-time progress updates via WebSocket

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Shubham**
- GitHub: [@Shubham30000](https://github.com/Shubham30000)
- LinkedIn: [Add your LinkedIn URL here]
- Email: [Add your email here]

## 🙏 Acknowledgments

- **IIT Madras TDS Course** for the project specifications
- **OpenRouter/AIPipe** for LLM API access
- **HuggingFace** for free hosting infrastructure
- **FastAPI & Playwright** communities for excellent documentation

## 📞 Contact

For questions or collaboration opportunities, feel free to reach out via GitHub issues or email.

---

⭐ If you find this project interesting, please consider giving it a star!

**Built with ❤️ for learning and innovation**