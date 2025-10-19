"""
backend/app.py

Flask server exposing:
 - GET  /         -> health check
 - POST /analyze  -> { "text": "..." } -> returns analysis JSON
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

# Import analyze_text from ai_model.py
from ai_model import analyze_text

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return jsonify({"status": "ok", "service": "PhishNet backend"})

@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not text or not text.strip():
        return jsonify({"error": "No text provided"}), 400

    try:
        result = analyze_text(text)
        return jsonify(result)
    except Exception as e:
        # Return debug info for hackathon; remove stack/trace in production
        print("Exception in /analyze endpoint:")
        traceback.print_exc()   # <-- prints full Python traceback
        return jsonify({"status": "analysis_failed", "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
