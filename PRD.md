# PRD: Ayurvedic Research Plagiarism Detection Tool

**Version:** 1.0  
**Date:** April 28, 2026  
**Status:** Draft

---

## 1. Problem Statement

### 1.1 The Challenge of Plagiarism in Ayurvedic Research

Plagiarism detection in Ayurvedic research is substantially harder than in conventional biomedical literature. Several domain-specific characteristics make standard detection tools ineffective or misleading:

**Sanskrit and Transliterated Terminology**  
Ayurvedic texts are saturated with Sanskrit terms (*Prakriti*, *Dosha*, *Vata*, *Pitta*, *Kapha*, *Rasayana*, *Panchakarma*) that appear identically across all legitimate papers in the field. Standard similarity algorithms flag these as matches even when the surrounding research is entirely original. False positives undermine trust in detection tools and create friction for editors.

**Ancient Text Citations — Repetitive by Nature**  
Classical references to the Charaka Samhita, Sushruta Samhita, Ashtanga Hridayam, Ashtanga Sangraha, and Kashyapa Samhita appear in nearly every Ayurvedic research article. Direct shloka quotations in Sanskrit, along with their transliterations and translations, are considered proper academic citation — not plagiarism — yet word-for-word classical quotes register as high-similarity in generic tools.

**Paraphrasing of Traditional Knowledge**  
The Ayurvedic knowledge base is ancient and finite. Researchers frequently describe the same classical concepts using slightly varied language. Distinguishing legitimate academic restatement of canonical knowledge from actual paraphrasing of a peer's work requires semantic and contextual judgment beyond n-gram matching.

**Multilingual and Code-Switched Content**  
Ayurvedic research articles often blend English prose with Sanskrit shlokas (sometimes in Devanagari script), Hindi transliterations, and Latin botanical names. This multi-script, multilingual nature breaks tokenization and similarity pipelines designed for monolingual corpora.

**No Centralized Ayurvedic Corpus**  
Unlike PubMed for biomedical research, there is no authoritative, searchable, machine-readable corpus of all published Ayurvedic research. Journals like JAIM, Ancient Science of Life, and AYU are partially indexed but not uniformly available for cross-referencing.

---

## 2. Target Users

| User Segment | Primary Need | Context |
|---|---|---|
| **Ayurvedic Journal Editors** | Screen submissions before review | Monthly submission volume; need fast, reliable signals |
| **Ayurvedic Researchers & PhD Students** | Self-check before submission | Unintentional overlap with classical sources |
| **Academic Institutions (NIA, IPGT&RA, GAU)** | Validate thesis chapters | Compliance with UGC norms |
| **AYUSH Ministry Affiliated Bodies** | Quality assurance for funded research | Grant-linked publication requirements |
| **Research Supervisors / Guides** | Review student work | Multiple students, need readable reports |

**Primary persona:** A journal editor at an Ayurvedic research publication who receives 40–80 submissions per month and needs a domain-aware report they can act on in under 5 minutes per article.

---

## 3. Core Features — v1 Scope

### 3.1 Input Methods
- **Text paste:** User pastes article text (up to ~5,000 words)
- **URL fetch:** User provides a URL to a publicly accessible article

### 3.2 Content Preprocessing
- Sentence segmentation into analysis units
- Soft-exclusion of Sanskrit/Ayurvedic terms from raw similarity scoring
- Identification of classical text citation patterns (CS, SS, AH, AS)
- Devanagari script detection (flagged separately; not scored in v1)

### 3.3 Semantic Similarity Analysis (Claude API)
- Send extracted passages to `claude-sonnet-4-20250514` with a domain-aware prompt
- Claude distinguishes between:
  - Legitimate classical citations (expected, not flagged)
  - Repetitive domain vocabulary (expected, not flagged)
  - Suspicious paraphrasing of another researcher's original analysis
  - Direct copying of non-classical material

### 3.4 Web Cross-Referencing
- Extract 5–10 "fingerprint" phrases from the article
- Query Serper API for each phrase
- Retrieve top matching URLs and excerpts
- Feed matched excerpts back to Claude for final similarity judgment

### 3.5 Plagiarism Score and Report
- **Overall score:** 0–100%
- **Passage-level highlights:** Color-coded (green = original, yellow = possible, red = flagged)
- **Matched sources list:** URL, title, matched excerpt, confidence level
- **Plain-English explanation:** Claude-generated guidance for the editor

### 3.6 Domain-Aware False Positive Suppression
- Predefined allowlist of Ayurvedic terminology and classical text abbreviations
- Classical shloka quotations with proper citation markers labeled "Classical Reference — Expected"

---

## 4. Out of Scope — v1

| Feature | Rationale |
|---|---|
| Real-time database of Ayurvedic journals | Requires licensing agreements; v2 target |
| Sanskrit OCR / Devanagari text extraction from PDFs | Specialized pipeline; v2 target |
| Multi-file batch upload | v2 after single-file validation |
| User accounts and authentication | Not needed for MVP |
| PDF upload and parsing | Text paste covers core use case |
| Self-plagiarism detection against user's own corpus | Requires user accounts; v2 |

---

## 5. Technical Approach

### 5.1 Architecture

```
Browser (Frontend)
    │
    ├── HTML + Tailwind CSS (static, served from Vercel)
    └── Vanilla JS (fetch API)
           │ relative /api/* calls
           ▼
    Vercel Serverless Functions (Python)
    ├── /api/analyze        — main analysis endpoint
    └── /api/fetch-url      — URL content extraction
           │
           ├── Anthropic Claude API (claude-sonnet-4-20250514)
           │     └── Semantic analysis + explanation generation
           └── Serper API
                 └── Web cross-referencing
```

### 5.2 Frontend
- **Stack:** HTML5 + Tailwind CSS (CDN) + Vanilla JavaScript
- No build step — single `index.html` at repo root
- Calls relative `/api/*` URLs (same-origin on Vercel)

### 5.3 Backend
- **Stack:** Python 3.9 Vercel serverless functions (`BaseHTTPRequestHandler`)
- **Key dependencies:** `anthropic`, `httpx`, `beautifulsoup4`
- Stateless — no database in v1

### 5.4 AI Integration — Claude API
- **Model:** `claude-sonnet-4-20250514`
- **Two-pass pipeline:**
  1. First pass: full article → get fingerprint queries + initial analysis
  2. Second pass: article + web evidence → final report
- **Prompt caching:** System prompt cached with `cache_control: ephemeral`

### 5.5 Hosting
| Component | Platform |
|---|---|
| Frontend + API | Vercel (single deploy) |
| Secrets | Vercel Environment Variables |

---

## 6. Success Metrics

| Metric | Target |
|---|---|
| Response time | < 15 seconds for a 2,000-word article |
| Score range | Clear 0–100% output for every valid input |
| End-to-end smoke test | At least 1 real Ayurvedic article input works |
| False positive rate | Classical Sanskrit terms don't drive score above 10% on original work |
| Report readability | Non-technical editor can act on report without additional guidance |

---

## 7. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Serper API rate limits | Cache results; cap to 6 queries per analysis |
| Claude returns inconsistent JSON | Parse with fallback schema; validate before rendering |
| URL fetch blocked by paywalls | Show clear error; encourage text paste as primary method |
| Vercel function cold start | Show loading state with step indicators |

---

*This document is a living spec. Update version number and date with each substantive revision.*
