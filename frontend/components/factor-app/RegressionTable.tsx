import type { AnalyzeResponse } from "@/lib/types";

type Props = {
  result: AnalyzeResponse;
};

const SIG_COLORS: Record<string, string> = {
  "***": "text-emerald-400",
  "**": "text-yellow-400",
  "*": "text-orange-400",
  "": "text-slate-600",
};

function fmtBeta(v: number) {
  return v >= 0 ? `+${v.toFixed(4)}` : v.toFixed(4);
}

function fmtPval(v: number) {
  return v < 0.001 ? "<0.001" : v.toFixed(3);
}

export default function RegressionTable({ result }: Props) {
  const { coefficients, r2, adj_r2, n_obs, date_range, se_type } = result;

  return (
    <div className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#2a2d3e]">
        <span className="text-xs text-slate-400">
          {result.ticker} · {result.model.toUpperCase()} · {date_range.start} – {date_range.end}
        </span>
        <span className="text-xs text-slate-600 bg-[#0f1117] px-2 py-0.5 rounded border border-[#2a2d3e]">
          {se_type === "HAC" ? "Newey-West SE" : "OLS SE"}
        </span>
      </div>

      <table className="w-full text-xs">
        <thead>
          <tr className="text-slate-500 border-b border-[#2a2d3e]">
            <th className="text-left px-4 py-2 font-normal">Factor</th>
            <th className="text-right px-4 py-2 font-normal">Beta</th>
            <th className="text-right px-4 py-2 font-normal">t-stat</th>
            <th className="text-right px-4 py-2 font-normal">p-value</th>
            <th className="text-right px-4 py-2 font-normal">Sig</th>
          </tr>
        </thead>
        <tbody>
          {coefficients.map((c) => (
            <tr
              key={c.name}
              className={`border-b border-[#2a2d3e]/50 hover:bg-[#0f1117]/50 ${
                c.name === "Alpha" ? "bg-[#0f1117]/30" : ""
              }`}
            >
              <td className="px-4 py-2.5 text-slate-300 font-medium">{c.name}</td>
              <td className="px-4 py-2.5 text-right text-slate-100 tabular-nums">
                {fmtBeta(c.beta)}
              </td>
              <td className="px-4 py-2.5 text-right text-slate-400 tabular-nums">
                {c.tstat.toFixed(2)}
              </td>
              <td className="px-4 py-2.5 text-right text-slate-400 tabular-nums">
                {fmtPval(c.pvalue)}
              </td>
              <td className={`px-4 py-2.5 text-right font-bold ${SIG_COLORS[c.sig]}`}>
                {c.sig || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex items-center justify-between px-4 py-3 border-t border-[#2a2d3e] text-xs text-slate-500">
        <span>
          R² <span className="text-slate-300">{r2.toFixed(4)}</span>
          <span className="mx-3">|</span>
          Adj R² <span className="text-slate-300">{adj_r2.toFixed(4)}</span>
        </span>
        <span>N = {n_obs} months</span>
      </div>
    </div>
  );
}
