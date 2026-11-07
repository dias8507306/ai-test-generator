# EduGen Pro: AI test generator for teachers

A test and quiz generator for school teachers. You pick a subject, topic, grade and difficulty, and it produces multiple-choice tasks with the correct answer, an explanation, a descriptor, assessment criteria and a Bloom's-taxonomy level. Tests can be saved and exported to PDF or DOCX. Several backends are included, from a local LLM (Ollama, Phi-3) to OpenAI and a fully offline knowledge-base generator.

## Features

- **EduGen Pro (`app.py`, Flask):**
  - registration / login (passwords hashed with Werkzeug scrypt), per-user history of saved tests
  - UI in three languages (KZ / RU / EN)
  - generation through a **local LLM** (Ollama, `phi3:mini`) with a JSON-format prompt that includes Bloom levels and descriptors
  - export of a test to **PDF** (ReportLab) and **DOCX** (python-docx)
- **SPA (`index.html`) + `http.server` backends** (all on port 8000):
  - `simple_server.py`: offline, uses a built-in knowledge base (informatics, maths, ...), **no key needed**
  - `ai_test_generator_fast.py`: fast template-based generator, no key needed
  - `server_final.py`: OpenAI chat-completions generator plus a JSON "database" of users and tasks (`data/`)
  - `server_ai_real.py`: OpenAI / DeepSeek / Gemini variant
- `ai_test_maker.py`: CLI generator through Ollama (`llama3.2`)
- `java-webserver/`: a small personal site served by a pure-Java `com.sun.net.httpserver` server (pages, static files, contact-form API)

## Tech stack

Python · Flask · Ollama (Phi-3 Mini / Llama 3.2) · OpenAI API (optional) · ReportLab · python-docx · vanilla HTML/CSS/JS · Java 8+ (`HttpServer`)

## Project structure

```
app.py                     EduGen Pro (Flask, Ollama, PDF/DOCX export)
index.html                 SPA frontend for the http.server backends
simple_server.py           offline generator (knowledge base)
ai_test_generator_fast.py  fast local generator
server_final.py            OpenAI generator + users/tasks JSON storage
server_ai_real.py          OpenAI / DeepSeek / Gemini variant
ai_test_maker.py           CLI generator (Ollama)
data/tasks.json            sample generated tasks
examples/task_bank.json    sample output of EduGen Pro
java-webserver/            Java HttpServer site (WebServer.java, SimpleWebServer.java, page1-3.html)
.env.example
```

## How to run

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

**Demo without any keys:**

```bash
python simple_server.py          # open http://localhost:8000
```

**EduGen Pro with a local LLM:**

```bash
ollama pull phi3:mini            # https://ollama.com, keep `ollama serve` running
python app.py                    # http://127.0.0.1:5000, demo login: admin@example.com / 123456
```

**OpenAI backend:** copy `.env.example` to `.env` (or export the variables), set `OPENAI_API_KEY`, then run `python server_final.py`.

**Java site:**

```bash
cd java-webserver
javac *.java && java WebServer   # http://localhost:8080
```

> All data in this repository is randomly generated; brand names are anonymized. No API keys are included; set your own through environment variables.

Author: Dias Ayazbay.

## Қысқаша (KZ)

EduGen Pro: мұғалімдерге арналған тест генераторы. Пән, тақырып, сынып және күрделілік бойынша Bloom таксономиясына сай тапсырмалар жасайды.
Жергілікті LLM (Ollama, Phi-3), OpenAI немесе кілтсіз офлайн режимде жұмыс істейді.
Тесттерді сақтауға және PDF/DOCX форматында жүктеп алуға болады. API кілттері тек айнымалы орта арқылы беріледі.
