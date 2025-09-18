# MockMate — AI Mock Interview App

A small Flask web app that generates interview questions, collects answers, and evaluates candidate responses using the Groq LLM API. The UI is built with simple Jinja2 templates and stores session data in `answers.json`.

## Features
- Generate role/position-specific interview questions
- Step through questions in a mock interview UI
- Store answers per-session in `answers.json`
- Evaluate answers using Groq LLM and show a structured result (score, strengths, weaknesses, tips)

## Repository Structure

```
hack/
├─ app.py                # Flask app (routes + storage helpers)
├─ model.py              # LLM integration (Groq client wrappers)
├─ answers.json          # Persistent session store for questions/answers/evaluations
├─ .env                  # Environment variables (GROQ_API_KEY, FLASK_SECRET)
├─ templates/
│  ├─ filldata.html      # Start form (role, position, extra, num questions)
│  ├─ interview.html     # Interview UI (shows questions, collects answers)
│  └─ result.html        # Evaluation display (score, strengths, weaknesses, tips, QA)
└─ README.md
```

## Prerequisites
- Python 3.10+
- A virtual environment (recommended)
- Groq API key with access to a supported model

## Setup

1. Create and activate a virtual environment

PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

If you don't have `requirements.txt`, install minimal packages:

```powershell
pip install flask python-dotenv groq requests
```

3. Add environment variables

Create a `.env` file in the project root with:

```
GROQ_API_KEY=your_groq_api_key_here
FLASK_SECRET=your-flask-secret
```

4. Run the app

```powershell
python app.py
```

Open `http://127.0.0.1:5000/` in your browser.

## How It Works

- `app.py` provides the HTTP routes:
  - `/` → `filldata.html` (start page)
  - `POST /start` → generates questions using `model.generate_questions`, creates a session, stores questions in `answers.json`, then redirects to `/interview/<session_id>`
  - `GET /interview/<session_id>` → shows the current question and UI
  - `POST /answer/<session_id>` → AJAX endpoint: stores the submitted answer, advances to next question or calls `model.evaluate_answers` when complete
  - `GET /result/<session_id>` → displays `result.html` once evaluation is ready

- `model.py` integrates with the Groq client to:
  - Generate questions (`generate_questions`)
  - Evaluate answers and return a structured `raw_evaluation` string (`evaluate_answers`)

- `answers.json` stores per-session data like questions, answers, current_index, meta and evaluation.

## Templates / UI Notes

- `filldata.html` — modern form with role/position/extra/num_questions
- `interview.html` — shows cleaned question text, progress bar, text-to-speech, and sends answers via AJAX
- `result.html` — parses the `raw_evaluation` returned by the model and displays:
  - Overall score
  - Key strengths
  - Areas for improvement
  - Tips to improve
  - Detailed Q/A list

The templates include defensive parsing to handle imperfect LLM output, but the evaluator prompt in `model.py` forces a consistent format.

## Troubleshooting

- 404 errors when calling LLM endpoints: check your `GROQ_MODEL` (use a supported model) and ensure your API key is valid.
- `UndefinedError` in templates: this usually means the evaluator response didn't match the expected format. Re-run evaluation or check `answers.json` for `evaluation` content.
- If the model returns text with extra introduction lines, the `interview.html` cleanup strips common patterns (e.g., "Here are 5 questions...").

## Security & Best Practices

- Do NOT commit `.env` or API keys to version control. Add `.env` to `.gitignore`.
- For production, use a proper session store (Redis) and secure secrets management.
- Consider rate-limiting LLM calls and adding async handling if evaluation becomes slow.

## Extending

- Swap `model.py` to use a different provider or add local model support.
- Persist session metadata to a real DB instead of `answers.json`.
- Add user accounts and multiple interviews per user.

## Next Steps I Recommend

1. Add `requirements.txt` listing `Flask`, `python-dotenv`, `groq`, `requests`.
2. Add `.gitignore` with `.env`, `__pycache__/`, `.venv/`, `*.pyc`.
3. Test a full interview flow and confirm `result.html` parses the `raw_evaluation` correctly.

If you want, I can:
- Run small fixes to templates or `model.py` formatting prompts.
- Add `requirements.txt` and `.gitignore` files.
# MockMate — AI Interview Coach (Flask + Hugging Face)

## Overview
MockMate is a small Flask app that:
- Accepts role, position, extra details, and number of questions.
- Uses Hugging Face Inference API to **generate interview questions**.
- Presents questions one-by-one with browser text-to-speech.
- Stores answers temporarily in `answers.json`.
- Sends collected Q&A to Hugging Face for a **structured evaluation** (score, strengths, weaknesses, tips, per-question feedback).

## Setup

1. **Clone / copy project files** into a folder `MockMate/`.

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
