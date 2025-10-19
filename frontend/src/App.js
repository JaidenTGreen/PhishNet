// src/App.js
import React, { useState } from "react";
import ResultCard from "./components/ResultCard";
import "./App.css";

export default function App() {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async () => {
    if (!subject.trim() && !body.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:5001/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: `Subject: ${subject}\n\n${body}` })
      });
      const j = await res.json();
      if (!res.ok) setError(j.error || "Server error");
      else setResult(j);
    } catch (e) {
      setError("Network error: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const clearAll = () => {
    setSubject("");
    setBody("");
    setResult(null);
    setError(null);
  };

  return (
    <div className="app">
      <header className="header">
        <h1>PhishNet — Email Scam Detector</h1>
      </header>

      <main className="main">
        <p>Enter the subject and message body below, then click Analyze.</p>

        <div className="input-group">
          <label>Subject</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Enter email subject"
          />
        </div>

        <div className="input-group">
          <label>Message Body</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Enter full email body here..."
          />
        </div>

        <div className="buttons">
          <button onClick={analyze} disabled={loading} className="button-primary">
            {loading ? "Analyzing..." : "Analyze"}
          </button>
          <button onClick={clearAll} className="button-secondary">
            Clear
          </button>
        </div>

        {error && <div className="error">{error}</div>}
        {result && <ResultCard result={result} />}
      </main>
    </div>
  );
}
