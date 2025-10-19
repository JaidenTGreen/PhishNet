// frontend/src/components/ResultCard.js
import React from "react";

const colorFor = (level) => {
  if (level === "Safe") return "bg-green-50 border-green-400 text-green-800";
  if (level === "Suspicious") return "bg-yellow-50 border-yellow-400 text-yellow-800";
  if (level === "Dangerous") return "bg-red-50 border-red-400 text-red-800";
  return "bg-gray-50 border-gray-300 text-gray-800";
};

export default function ResultCard({ result }) {
  return (
    <div className={`p-4 border-l-4 ${colorFor(result.risk_level)}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Risk: {result.risk_level}</h2>
        <span className="text-sm">Score: {result.score}/100</span>
      </div>
      <div className="mt-3">
        <h3 className="font-medium">Reasons</h3>
        <ul className="list-disc ml-6">
          {result.reasons?.length ? result.reasons.map((r,i)=><li key={i}>{r}</li>) : <li>No reasons returned</li>}
        </ul>
      </div>
      {result.suspicious_links?.length > 0 && (
        <div className="mt-3">
          <h3 className="font-medium">Suspicious Links</h3>
          <ul className="ml-4">
            {result.suspicious_links.map((l,i)=>(
              <li key={i}><code className="break-all">{l.url}</code> {l.problem ? <span className="text-sm text-gray-600"> — {l.problem}</span> : null}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
