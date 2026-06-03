"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

type Props = {
  figure: object;
  title?: string;
  className?: string;
};

export default function PlotlyChart({ figure, title, className }: Props) {
  if (!figure || Object.keys(figure).length === 0) return null;

  const fig = figure as { data?: unknown[]; layout?: Record<string, unknown> };

  return (
    <div className={`bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg overflow-hidden ${className ?? ""}`}>
      {title && (
        <div className="px-4 py-3 border-b border-[#2a2d3e]">
          <span className="text-xs text-slate-400">{title}</span>
        </div>
      )}
      <Plot
        data={(fig.data ?? []) as Plotly.Data[]}
        layout={{
          ...(fig.layout ?? {}),
          autosize: true,
          paper_bgcolor: "transparent",
          plot_bgcolor: "#1a1d2e",
          margin: { l: 50, r: 20, t: 20, b: 40 },
          font: { color: "#94a3b8", size: 11 },
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", minHeight: "280px" }}
        useResizeHandler
      />
    </div>
  );
}
