import type { AnalyzeResponse } from "@/lib/types";

type Props = {
  result: AnalyzeResponse;
};

export default function AlphaVerdict({ result }: Props) {
  const alphaSig = result.coefficients.find((c) => c.name === "Alpha");
  const isSignificant = alphaSig && alphaSig.pvalue < 0.05;

  const borderColor = isSignificant ? "border-yellow-500/40" : "border-emerald-500/40";
  const dotColor = isSignificant ? "bg-yellow-400" : "bg-emerald-400";
  const label = isSignificant ? "⚠ Alpha detected — verify for data issues" : "Alpha: statistically zero";

  const [ciLow, ciHigh] = result.alpha_ci;

  return (
    <div className={`bg-[#1a1d2e] border ${borderColor} rounded-lg p-4 space-y-2`}>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${dotColor} flex-shrink-0`} />
        <span className="text-xs font-semibold text-slate-300">{label}</span>
      </div>
      <p className="text-xs text-slate-400 leading-relaxed">{result.verdict}</p>
      <p className="text-xs text-slate-600">
        95% CI:{" "}
        <span className="text-slate-400">
          [{(ciLow * 100).toFixed(3)}%, {(ciHigh * 100).toFixed(3)}%] / month
        </span>
      </p>
    </div>
  );
}
