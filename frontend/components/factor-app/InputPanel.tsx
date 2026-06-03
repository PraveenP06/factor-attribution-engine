"use client";

import { useState } from "react";
import type { AnalyzeRequest, ModelType, WeightedTicker } from "@/lib/types";

type Props = {
  onSubmit: (req: AnalyzeRequest) => void;
  loading: boolean;
};

const MODELS: { value: ModelType; label: string }[] = [
  { value: "ff3", label: "FF3" },
  { value: "ff4", label: "FF4 (Carhart)" },
  { value: "ff5", label: "FF5" },
];

export default function InputPanel({ onSubmit, loading }: Props) {
  const [mode, setMode] = useState<"single" | "portfolio">("single");
  const [ticker, setTicker] = useState("AAPL");
  const [model, setModel] = useState<ModelType>("ff3");
  const [start, setStart] = useState("2015-01");
  const [end, setEnd] = useState("2024-12");
  const [neweyWest, setNeweyWest] = useState(true);
  const [holdings, setHoldings] = useState<WeightedTicker[]>([
    { ticker: "AAPL", weight: 0.4 },
    { ticker: "MSFT", weight: 0.3 },
    { ticker: "GOOGL", weight: 0.3 },
  ]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (mode === "single") {
      onSubmit({ mode, tickers: [ticker.toUpperCase()], model, start, end, newey_west: neweyWest });
    } else {
      const totalWeight = holdings.reduce((s, h) => s + h.weight, 0);
      if (Math.abs(totalWeight - 1.0) > 0.01) {
        alert(`Weights sum to ${(totalWeight * 100).toFixed(1)}% — must be 100%`);
        return;
      }
      onSubmit({ mode, tickers: holdings, model, start, end, newey_west: neweyWest });
    }
  }

  function updateHolding(i: number, field: keyof WeightedTicker, value: string) {
    setHoldings((prev) => {
      const updated = [...prev];
      updated[i] = {
        ...updated[i],
        [field]: field === "weight" ? parseFloat(value) || 0 : value,
      };
      return updated;
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg p-5 space-y-4"
    >
      <div className="flex gap-1 text-xs">
        {(["single", "portfolio"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={`px-3 py-1 rounded border transition-colors ${
              mode === m
                ? "border-indigo-500 bg-indigo-500/10 text-indigo-400"
                : "border-[#2a2d3e] text-slate-500 hover:text-slate-300"
            }`}
          >
            {m}
          </button>
        ))}
      </div>

      {mode === "single" ? (
        <div>
          <label className="text-xs text-slate-500 block mb-1">Ticker</label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="AAPL"
            className="w-full bg-[#0f1117] border border-[#2a2d3e] rounded px-3 py-2 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 focus:outline-none uppercase"
          />
        </div>
      ) : (
        <div className="space-y-2">
          <label className="text-xs text-slate-500 block">Portfolio</label>
          {holdings.map((h, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={h.ticker}
                onChange={(e) => updateHolding(i, "ticker", e.target.value)}
                className="flex-1 bg-[#0f1117] border border-[#2a2d3e] rounded px-3 py-1.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none uppercase"
                placeholder="AAPL"
              />
              <input
                type="number"
                value={h.weight}
                step="0.05"
                min="0"
                max="1"
                onChange={(e) => updateHolding(i, "weight", e.target.value)}
                className="w-20 bg-[#0f1117] border border-[#2a2d3e] rounded px-3 py-1.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => setHoldings((prev) => prev.filter((_, j) => j !== i))}
                className="text-slate-600 hover:text-red-400 text-xs px-2"
              >
                ✕
              </button>
            </div>
          ))}
          <div className="flex justify-between items-center text-xs">
            <button
              type="button"
              onClick={() => setHoldings((prev) => [...prev, { ticker: "", weight: 0 }])}
              className="text-indigo-400 hover:text-indigo-300"
            >
              + add ticker
            </button>
            <span className={`${Math.abs(holdings.reduce((s, h) => s + h.weight, 0) - 1) > 0.01 ? "text-red-400" : "text-emerald-400"}`}>
              {(holdings.reduce((s, h) => s + h.weight, 0) * 100).toFixed(0)}% allocated
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs text-slate-500 block mb-1">Start</label>
          <input
            type="month"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="w-full bg-[#0f1117] border border-[#2a2d3e] rounded px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="text-xs text-slate-500 block mb-1">End</label>
          <input
            type="month"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="w-full bg-[#0f1117] border border-[#2a2d3e] rounded px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none"
          />
        </div>
      </div>

      <div>
        <label className="text-xs text-slate-500 block mb-1">Factor Model</label>
        <div className="flex gap-1">
          {MODELS.map((m) => (
            <button
              key={m.value}
              type="button"
              onClick={() => setModel(m.value)}
              className={`px-3 py-1 rounded border text-xs transition-colors ${
                model === m.value
                  ? "border-indigo-500 bg-indigo-500/10 text-indigo-400"
                  : "border-[#2a2d3e] text-slate-500 hover:text-slate-300"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <label className="flex items-center gap-2 cursor-pointer select-none">
        <div
          onClick={() => setNeweyWest((v) => !v)}
          className={`w-8 h-4 rounded-full transition-colors relative ${neweyWest ? "bg-indigo-500" : "bg-[#2a2d3e]"}`}
        >
          <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-transform ${neweyWest ? "translate-x-4" : "translate-x-0.5"}`} />
        </div>
        <span className="text-xs text-slate-400">Newey-West HAC standard errors</span>
      </label>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2 rounded bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold text-white transition-colors"
      >
        {loading ? "Analyzing..." : "Analyze →"}
      </button>
    </form>
  );
}
