import type { Finding } from "../../types";
import { SeverityBadge, severityColor } from "../ui/Badges";

export function FindingCard({ finding }: { finding: Finding }) {
  const location = finding.file + (finding.line_number ? `:${finding.line_number}` : "");
  return (
    <div className="finding-card" style={{ borderLeftColor: severityColor(finding.severity) }}>
      <div className="finding-head">
        <SeverityBadge severity={finding.severity} />
        <span className="issue-title">{finding.issue}</span>
      </div>
      <div className="file-path" style={{ marginTop: 6 }}>
        {location} &middot; {finding.agent}
      </div>
      <dl>
        {finding.explanation && (
          <>
            <dt>Why it matters</dt>
            <dd>{finding.explanation}</dd>
          </>
        )}
        {finding.impact && (
          <>
            <dt>Impact</dt>
            <dd>{finding.impact}</dd>
          </>
        )}
        {finding.recommendation && (
          <>
            <dt>Recommendation</dt>
            <dd>{finding.recommendation}</dd>
          </>
        )}
      </dl>
      <div className="confidence">Confidence: {Math.round(finding.confidence * 100)}%</div>
    </div>
  );
}
