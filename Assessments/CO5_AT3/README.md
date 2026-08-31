# AI Meeting Summarization Application

FastAPI + Streamlit meeting summarizer with a built-in prompt-injection security demo (vulnerable vs. secure modes).

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Groq API key (get one free at https://console.groq.com):

```bash
cp .env.example .env
# edit .env and set GROQ_API_KEY
export GROQ_API_KEY="your-key-here"   # or `source .env` if using python-dotenv
```

The app **also runs without a key** — it falls back to a clearly labeled `DEMO STUB` response, so you can still test and demonstrate the validation and injection-detection layers without needing a live LLM key.

## Run

Terminal 1 — backend:
```bash
uvicorn api:app --reload --port 8000
```

Terminal 2 — frontend:
```bash
streamlit run app.py
```

- Streamlit UI: http://localhost:8501
- FastAPI interactive docs: http://localhost:8000/docs

## Try the security demo

1. In the sidebar, switch between **Secure** and **Vulnerable** mode.
2. Paste the example injection payload shown in the sidebar (or type your own) into the transcript box.
3. Click Summarize.
4. Compare the warning banners:
   - **Vulnerable mode** shows a yellow warning: injection detected but *not* blocked.
   - **Secure mode** shows a blue notice: injection detected *and* isolated — it cannot affect the output because the transcript is passed to the model as clearly delimited data, not instructions.

## File Structure

```
meeting_app/
├── api.py            FastAPI endpoints (/summarize/vulnerable, /summarize/secure)
├── app.py             Streamlit UI
├── config.py           Prompts, limits, injection-detection patterns
├── utils.py            Validation, injection detection, output sanitization
├── requirements.txt
├── .env.example
└── README.md
```

## Switching LLM providers

All LLM calls go through one function: `call_llm()` in `api.py`. It currently calls Groq's `llama-3.3-70b-versatile`. To use Anthropic's Claude instead (as in the original project brief), replace the body of that function with an Anthropic API call using `ANTHROPIC_API_KEY` from `config.py` — no other file needs to change.

## Testing

Run the security-layer test harness directly (no server needed):

```bash
python utils.py
```

This runs 7 real test cases (normal input, empty, whitespace, too-short, two injection payloads, too-long) through validation and injection detection, printing real pass/fail/flagged results for each.
