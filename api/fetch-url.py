import json
import re
import httpx
from bs4 import BeautifulSoup
from http.server import BaseHTTPRequestHandler


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text)[:8000]


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
            url = body.get("url", "").strip()

            if not url:
                self.send_json({"detail": "URL is required."}, 422)
                return

            headers = {"User-Agent": "Mozilla/5.0 (compatible; AyurvedaPlagiarismDetector/1.0)"}
            with httpx.Client(timeout=15, follow_redirects=True) as hc:
                resp = hc.get(url, headers=headers)
                resp.raise_for_status()
                text = extract_text(resp.text)

            if len(text.strip()) < 100:
                self.send_json(
                    {"detail": "Extracted text too short — the URL may require login or is blocking bots."},
                    422,
                )
                return

            self.send_json({"text": text, "char_count": len(text)})

        except httpx.HTTPStatusError as e:
            self.send_json({"detail": f"URL fetch failed: HTTP {e.response.status_code}"}, 400)
        except httpx.RequestError as e:
            self.send_json({"detail": f"URL fetch error: {str(e)}"}, 400)
        except Exception as e:
            self.send_json({"detail": str(e)}, 500)
