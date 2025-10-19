"""
backend/ai_model.py

PhishNet analyzer:
 - heuristics_analyze(text)        -> deterministic checks (works offline)
 - call_llm_to_refine(text, heur) -> optional call to Gemini (if GEMINI_API_KEY set)
 - analyze_text(text)             -> public function returning final dict

Notes:
 - Keeps LLM usage optional and safe: if no API key or the LLM fails, heuristics result is returned.
 - The LLM call is designed to request a compact JSON response, and the code attempts to parse it.
 - Do NOT commit your .env (GEMINI_API_KEY) to source control.
"""

import os
import re
import json
from dotenv import load_dotenv
from urlextract import URLExtract
import tldextract

# Load .env from the same folder (backend/.env)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Try to import the official Google Gemini client if available.
# We wrap import in try/except so code still runs if package is not installed.
try:
    import google.generativeai as genai
    _HAS_GEMINI = True
    # configure at runtime using env var
    genai.configure(api_key=os.getenv("GEMINI_API_KEY") or "")
except Exception:
    _HAS_GEMINI = False

# Instantiate URL extractor (used by heuristics)
extractor = URLExtract()

def heuristics_analyze(text: str) -> dict:
    """
    Deterministic heuristic checks returning a well-formed dict:
    {
      "risk_level": "Safe"/"Suspicious"/"Dangerous",
      "score": int,
      "reasons": [ ... ],
      "suspicious_links": [{"url":"...","problem":"..."}]

    }
    """
    if not text:
        return {
            "risk_level": "Safe",
            "score": 0,
            "reasons": ["Empty message"],
            "suspicious_links": []
        }

    t = text.strip()
    t_low = t.lower()
    reasons = []
    score = 0

    # Urgency keywords
    urgent = ["urgent", "verify", "verify your", "immediately", "suspend", "suspended",
              "act now", "click below", "deadline", "your account has been suspended"]
    found_urgent = [w for w in urgent if w in t_low]
    if found_urgent:
        reasons.append(f"Urgency language: {', '.join(found_urgent[:5])}")
        score += 28

    # Requests for credentials / sensitive info
    sensitive = ["password", "credit card", "ssn", "social security", "account number",
    "acct number", "routing number", "bank number", "login", "verify identity"]
    found_sensitive = [w for w in sensitive if w in t_low]
    if found_sensitive:
        reasons.append(f"Requests sensitive info: {', '.join(found_sensitive[:5])}")
        score += 30

    # Excessive punctuation or ALL CAPS
    exclam = t.count("!")
    if exclam >= 2:
        reasons.append(f"Contains {exclam} exclamation mark(s)")
        score += 6
    if re.search(r"[A-Z]{6,}", t):
        reasons.append("Contains long ALL-CAPS word(s)")
        score += 5

    # Extract URLs and inspect
    urls = extractor.find_urls(t)
    suspicious_links = []
    shorteners = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "tiny.cc"]
    for u in urls:
        # normalize (if missing scheme)
        u_norm = u if u.startswith("http") else "http://" + u
        ext = tldextract.extract(u_norm)
        domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
        problem = None

        # IP address in URL
        if re.search(r"https?://\d+\.\d+\.\d+\.\d+", u_norm):
            problem = "IP address used in URL"
            score += 20

        # shortened
        if any(s in u_norm for s in shorteners):
            problem = (problem + "; shortened URL") if problem else "shortened URL"
            score += 12

        # suspicious domain pattern (multiple hyphens, lookalike)
        if domain and domain.count("-") >= 2:
            problem = (problem + "; suspicious domain pattern") if problem else "suspicious domain pattern"
            score += 6

        suspicious_links.append({"url": u, "domain": domain, "problem": problem})

    if suspicious_links:
        reasons.append(f"Found {len(suspicious_links)} link(s) — inspect domains")

    # If no strong indicators add a mild neutral reason
    if not reasons:
        reasons.append("No strong heuristic flags found")

    # clamp score
    score = max(0, min(100, score))

    # label mapping
    if score >= 60:
        label = "Dangerous"
    elif score >= 30:
        label = "Suspicious"
    else:
        label = "Safe"

    return {
        "risk_level": label,
        "score": int(score),
        "reasons": reasons,
        "suspicious_links": suspicious_links
    }


def _build_llm_prompt(text: str, heuristics_output: dict) -> str:
    """
    Craft a compact, explicit prompt that asks Gemini to return JSON only.
    Provide the heuristics output so the LLM can refine or explain.
    """
    prompt = f"""
You are a concise cybersecurity assistant. The user will provide an email message.
Task: Classify the email as one of: Safe, Suspicious, Dangerous.
Also return a numeric risk score 0-100, a short list of reasons, and a list of suspicious links with brief issues.

Important: Respond with VALID JSON only, matching this schema exactly:
{{
  "risk_level": "Safe|Suspicious|Dangerous",
  "score": 0-100,
  "reasons": ["string", "..."],
  "suspicious_links": [{{"url": "...", "problem": "..."}}]

}}

Email message:
\"\"\"{text} \"\"\"

Heuristics summary (for context):
{json.dumps(heuristics_output, indent=2)}

Return the JSON and nothing else.
"""
    return prompt


def call_llm_to_refine(text: str, heuristics_output: dict) -> dict:
    """
    If a Gemini/OpenAI API key is present and the package is available,
    call Gemini and attempt to parse JSON. On any failure, return heuristics_output.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key or not _HAS_GEMINI:
        # No key or library — return heuristics result
        return heuristics_output

    prompt = _build_llm_prompt(text, heuristics_output)

    try:
        # Example using google.generativeai package.
        # Different versions of the library may have slightly different methods.
        # We use a short call and expect textual JSON in the response.
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text_out = response.text.strip()

        # Try to find a JSON substring in the output
        # Some LLMs add backticks or explanation, so extract {...}
        json_start = text_out.find("{")
        json_end = text_out.rfind("}")
        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_text = text_out[json_start:json_end+1]
            parsed = json.loads(json_text)
            # Validate minimal fields and coerce types
            parsed_score = int(parsed.get("score", heuristics_output["score"]))
            parsed_level = parsed.get("risk_level", heuristics_output["risk_level"])
            parsed_reasons = parsed.get("reasons", heuristics_output.get("reasons", []))
            parsed_links = parsed.get("suspicious_links", heuristics_output.get("suspicious_links", []))

            # sanitize and return
            return {
                "risk_level": parsed_level,
                "score": max(0, min(100, parsed_score)),
                "reasons": parsed_reasons if isinstance(parsed_reasons, list) else [str(parsed_reasons)],
                "suspicious_links": parsed_links if isinstance(parsed_links, list) else heuristics_output.get("suspicious_links", [])
            }

        # If parsing failed, fall back to heuristics
        return heuristics_output

    except Exception as e:
        # On any error (network/key/parse) return heuristics result
        # In debugging you can log 'e' to server logs
        return heuristics_output


def analyze_text(text: str) -> dict:
    """
    Top-level function to use from the Flask route.
    Runs heuristics first then optionally asks the LLM to refine.
    """
    heur = heuristics_analyze(text)
    final = call_llm_to_refine(text, heur)
    return final
