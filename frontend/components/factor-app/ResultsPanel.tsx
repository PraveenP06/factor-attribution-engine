import type { AnalyzeResponse } from "@/lib/types";
import RegressionTable from "./RegressionTable";
import AlphaVerdict from "./AlphaVerdict";
import PlotlyChart from "./PlotlyChart";

type Props = {
  result: AnalyzeResponse;
};

export default function ResultsPanel({ result }: Props) {
  return (
    <div className="space-y-4">
      <RegressionTable result={result} />
      <AlphaVerdict result={result} />
      <PlotlyChart figure={result.factor_loadings_chart} title="Factor Loadings" />
      <PlotlyChart figure={result.actual_vs_predicted_chart} title="Actual vs Factor-Predicted Returns" />
      {result.rolling_betas && Object.keys(result.rolling_betas).length > 0 && (
        <PlotlyChart figure={result.rolling_beta_chart} title="Rolling Factor Betas (36-month window)" />
      )}
    </div>
  );
}
