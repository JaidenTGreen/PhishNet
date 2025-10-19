// frontend/src/App.js
import React, { useState } from "react";
import ResultCard from "./components/ResultCard"; // create this file under src/components

export default function App(){
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async () => {
    if (!text.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:5001/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
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

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-xl font-semibold">PhishNet — Email Scam Detector</h1>
      </header>
      <main className="max-w-3xl mx-auto p-6">
        <p className="mb-4 text-gray-700">Paste an email message below and click Analyze.</p>
        <textarea value={text} onChange={e=>setText(e.target.value)}
          className="w-full h-56 p-3 border rounded-md" placeholder="Paste full email text here..."/>
        <div className="mt-4 flex gap-2">
          <button onClick={analyze} disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded">{loading ? "Analyzing..." : "Analyze"}</button>
          <button onClick={()=>{setText(""); setResult(null); setError(null);}} className="bg-gray-200 px-4 py-2 rounded">Clear</button>
        </div>
        {error && <div className="mt-4 text-red-600">{error}</div>}
        {result && <div className="mt-6"><ResultCard result={result} /></div>}
      </main>
    </div>
  );
}
