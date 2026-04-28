import json
import os
import re
import httpx
import anthropic
from http.server import BaseHTTPRequestHandler

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

SYSTEM_PROMPT = """You are an expert in Ayurvedic medicine, Sanskrit texts, and academic plagiarism detection.

Your task is to analyze Ayurvedic research articles for potential plagiarism. You deeply understand:
- Classical Ayurvedic texts: Charaka Samhita (CS), Sushruta Samhita (SS), Ashtanga Hridayam (AH), Ashtanga Sangraha (AS), Kashyapa Samhita, Sharangadhara Samhita
- Standard Ayurvedic terminology (Dosha, Prakriti, Vata, Pitta, Kapha, Rasayana, Panchakarma, Churna, Vati, etc.)
- That Sanskrit shlokas with proper citations are EXPECTED and should NOT be flagged
- That domain-specific Ayurvedic vocabulary appearing across many papers is NORMAL and should NOT inflate the plagiarism score
- The difference between legitimate restatement of classical knowledge vs. copying another researcher's original analysis

When analyzing text:
1. IGNORE: Sanskrit/Ayurvedic terminology, classical shloka quotations with citations, standard botanical Latin names
2. FOCUS ON: Original analytical framing, research methodology descriptions, result interpretations, discussion paragraphs, conclusions
3. FLAG: Passages that appear copied or closely paraphrased from non-classical external sources

Always respond with valid JSON only, no markdown, no explanation outside the JSON."""


def serper_search(query):
    if not SERPER_API_KEY:
        return []
    try:
        with httpx.Client(timeout=10) as hc:
            resp = hc.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": query, "num": 5},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            return [
                {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
                for r in data.get("organic", [])[:5]
            ]
    except Exception:
        return []


def run_claude_analysis(article_text, web_evidence):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    web_evidence_text = ""
    if web_evidence:
        web_evidence_text = "\n\nWEB SEARCH EVIDENCE:\n"
        for i, ev in enumerate(web_evidence[:15], 1):
            web_evidence_text += (
                f"\n[{i}] Query: {ev.get('query','')}\n"
                f"Title: {ev.get('title','')}\n"
                f"URL: {ev.get('url','')}\n"
                f"Snippet: {ev.get('snippet','')}\n"
            )

    user_prompt = f"""Analyze the following Ayurvedic research article text for plagiarism.

ARTICLE TEXT:
{article_text[:5000]}
{web_evidence_text}

Return a JSON object with this exact structure:
{{
  "score": <integer 0-100, overall plagiarism percentage>,
  "score_explanation": "<1-2 sentences explaining what drove the score>",
  "flagged_passages": [
    {{
      "text": "<exact quote from the article, max 200 chars>",
      "reason": "<why this passage is suspicious>",
      "confidence": "<high|medium|low>",
      "matched_source": "<URL or 'Unknown' if no web match found>"
    }}
  ],
  "fingerprint_queries": [
    "<5-8 short phrases from the article suitable for web search>"
  ],
  "matched_sources": [
    {{
      "url": "<URL>",
      "title": "<page title>",
      "matched_excerpt": "<snippet that matched>",
      "relevance": "<high|medium|low>"
    }}
  ],
  "domain_terms_excluded": ["<Ayurvedic/Sanskrit terms detected and excluded from scoring>"],
  "classical_references_found": ["<classical text references found, e.g. CS Su. 1/1>"],
  "explanation": "<3-5 sentence plain-English summary for a journal editor explaining what was found and what action to take>"
}}

Score thresholds:
- 0-15: Minimal concern, original work
- 16-35: Some shared language, likely domain vocabulary or acceptable paraphrase
- 36-60: Notable similarity, warrants closer review
- 61-100: High similarity, strong plagiarism signal"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "score": 0,
            "score_explanation": "Analysis parsing error — please retry.",
            "flagged_passages": [],
            "fingerprint_queries": [],
            "matched_sources": [],
            "domain_terms_excluded": [],
            "classical_references_found": [],
            "explanation": raw[:500],
        }


class handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            text = body.get("text", "").strip()

            if len(text) < 100:
                self.send_json({"detail": "Article text is too short (minimum 100 characters)."}, 422)
                return

            text = text[:30000]

            # First pass — get fingerprint queries
            result = run_claude_analysis(text, [])
            fingerprints = result.get("fingerprint_queries", [])

            # Web search pass
            web_evidence = []
            if fingerprints and SERPER_API_KEY:
                for q in fingerprints[:6]:
                    hits = serper_search(q)
                    for h in hits:
                        h["query"] = q
                        web_evidence.append(h)

            # Second pass with web evidence
            if web_evidence:
                result = run_claude_analysis(text, web_evidence)

            # Merge any web hits Claude didn't capture
            existing_urls = {s["url"] for s in result.get("matched_sources", [])}
            for ev in web_evidence:
                if ev["url"] not in existing_urls and ev.get("snippet"):
                    result.setdefault("matched_sources", []).append({
                        "url": ev["url"],
                        "title": ev["title"],
                        "matched_excerpt": ev["snippet"],
                        "relevance": "medium",
                    })
                    existing_urls.add(ev["url"])

            self.send_json(result)

        except Exception as e:
            self.send_json({"detail": str(e)}, 500)
