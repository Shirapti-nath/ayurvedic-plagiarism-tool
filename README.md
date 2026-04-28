# Ayurvedic Plagiarism Detector

A domain-aware plagiarism detection tool for Ayurvedic research articles. Unlike generic tools, it understands classical Sanskrit citations, standard Ayurvedic terminology, and the repetitive nature of traditional knowledge references — preventing false positives while accurately flagging real similarity.

## Live URL

**[https://ayurvedic-plagiarism-tool.vercel.app](https://ayurvedic-plagiarism-tool.vercel.app)** *(update after Vercel deploy)*

---

## Features

- Paste article text or provide a public URL
- Claude AI (`claude-sonnet-4-20250514`) performs semantic plagiarism analysis
- Web cross-referencing via Serper API
- Sanskrit terms and classical shlokas (Charaka Samhita, Sushruta Samhita, etc.) excluded from scoring
- Color-coded flagged passages (red = high confidence, yellow = medium)
- 0–100% plagiarism score with plain-English editor guidance

---

## Project Structure

```
/
├── api/
│   ├── analyze.py        # Vercel Python serverless — main analysis
│   └── fetch-url.py      # Vercel Python serverless — URL extraction
├── index.html            # Frontend (HTML + Tailwind, no build step)
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies for Vercel
├── .env.example          # Required environment variables
└── PRD.md                # Product Requirements Document
```

---

## Deploy to Vercel (Recommended)

### 1. Fork this repo and import to Vercel

1. Fork this repository on GitHub
2. Go to [vercel.com](https://vercel.com) → **New Project** → Import your fork
3. Add environment variables in the Vercel dashboard:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `SERPER_API_KEY` | From [serper.dev](https://serper.dev) (free: 2,500 searches/month) |

4. Click **Deploy** — done.

---

## Local Development

### Prerequisites
- Python 3.9+
- [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`

### Setup

```bash
git clone https://github.com/Shirapti-nath/ayurvedic-plagiarism-tool.git
cd ayurvedic-plagiarism-tool
cp .env.example .env
# Edit .env and fill in your API keys
pip install -r requirements.txt
vercel dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

> `vercel dev` runs both the static frontend and the Python serverless functions locally on the same port — no separate backend process needed.

---

## How the Analysis Works

1. **Preprocessing** — article text is segmented; Devanagari script passages detected
2. **Initial AI pass** — Claude analyzes the full text and generates 5–8 "fingerprint" search queries
3. **Web cross-referencing** — Serper API searches each fingerprint phrase for matching web sources
4. **Final AI pass** — Claude re-evaluates with web evidence and produces the final report
5. **Score** — weighted blend of AI semantic confidence and web match density (0–100%)

---

## Limitations (v1)

- No PDF or Devanagari OCR — text paste for non-Latin scripts
- No private Ayurvedic journal database
- URL fetch may fail on paywalled or bot-protected pages
- Maximum ~5,000 words per submission
