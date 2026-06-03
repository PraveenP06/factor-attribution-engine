"use client";

import { useState } from "react";
import Link from "next/link";
import { analyze } from "@/lib/api";
import type { AnalyzeRequest, AnalyzeResponse } from "@/lib/types";
import InputPanel from "@/components/factor-app/InputPanel";
import ResultsPanel from "@/components/factor-app/ResultsPanel";

export default function FactorAttributionPage() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(req: AnalyzeRequest) {
    setLoading(true);
    setError(null);
    try {
      const data = await analyze(req);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[#2a2d3e] px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-slate-600 hover:text-slate-400 text-xs transition-colors">
            ← back
          </Link>
          <span className="text-slate-600 text-xs">|</span>
          <span className="text-sm text-slate-300 font-semibold">Factor Attribution Engine</span>
        </div>
        <span className="text-xs text-slate-600">
          Fama-French · Carhart · Newey-West HAC
        </span>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6">
        <aside>
          <InputPanel onSubmit={handleSubmit} loading={loading} />

          <div className="mt-4 p-4 bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg space-y-2">
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-widest">About</p>
            <p className="text-xs text-slate-500 leading-relaxed">
              Runs OLS regression of excess returns against factor returns:{" "}
              <span className="text-slate-400">R_i − R_f = α + β₁·MKT + β₂·SMB + β₃·HML + ε</span>
            </p>
            <p className="text-xs text-slate-500 leading-relaxed">
              Significance stars: <span className="text-emerald-400">*** p&lt;0.01</span>{" "}
              <span className="text-yellow-400">** p&lt;0.05</span>{" "}
              <span className="text-orange-400">* p&lt;0.10</span>
            </p>
          </div>
        </aside>

        <main>
          {error && (
            <div className="bg-red-950/40 border border-red-800/50 rounded-lg px-4 py-3 text-sm text-red-400 mb-4">
              {error}
            </div>
          )}

          {loading && (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg h-32 animate-pulse"
                />
              ))}
            </div>
          )}

          {!loading && !result && !error && (
            <div className="flex items-center justify-center h-64 text-slate-600 text-sm border border-dashed border-[#2a2d3e] rounded-lg">
              Enter a ticker and click Analyze →
            </div>
          )}

          {!loading && result && <ResultsPanel result={result} />}
        </main>
      </div>
    </div>
  );
}
