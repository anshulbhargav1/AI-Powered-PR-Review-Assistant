import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useRepositories } from "../context/RepositoriesContext";
import { useReview } from "../hooks/useReview";
import { CategoryBadge, StatusBadge } from "../components/ui/Badges";
import { Breadcrumbs } from "../components/ui/Breadcrumbs";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Icon } from "../components/ui/Icon";
import { SkeletonBlock, SkeletonLine } from "../components/ui/Skeleton";
import { FindingCard } from "../components/reviews/FindingCard";
import type { Category, Severity } from "../types";
import { formatDateTime } from "../utils/time";
import { formatRepoName } from "../utils/repo";

const CATEGORY_ORDER: Category[] = ["security", "performance", "code_quality", "testing"];
const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

export function ReviewDetail() {
  const { id } = useParams<{ id: string }>();
  const { review, error, reload } = useReview(id);
  const { repoById } = useRepositories();
  const [activeSeverities, setActiveSeverities] = useState<Set<Severity> | null>(null);

  const availableSeverities = useMemo(() => {
    if (!review) return [];
    const present = new Set(review.findings.map((f) => f.severity));
    return SEVERITY_ORDER.filter((s) => present.has(s));
  }, [review]);

  const effectiveActive = activeSeverities ?? new Set(availableSeverities);

  const toggleSeverity = (sev: Severity) => {
    const next = new Set(effectiveActive);
    if (next.has(sev)) next.delete(sev);
    else next.add(sev);
    setActiveSeverities(next);
  };

  if (error) {
    return <ErrorState message={error} onRetry={reload} />;
  }

  if (review === null) {
    return (
      <div>
        <SkeletonLine width="30%" />
        <div className="card" style={{ marginTop: 16 }}>
          <SkeletonLine width="50%" />
          <SkeletonLine width="35%" />
        </div>
        <div style={{ marginTop: 20 }}>
          <SkeletonBlock height={100} />
        </div>
      </div>
    );
  }

  const repo = repoById(review.repository_id);
  const filteredFindings = review.findings.filter((f) => effectiveActive.has(f.severity));

  return (
    <div>
      <Breadcrumbs items={[{ label: "Reviews", to: "/reviews" }, { label: review.title || `PR #${review.pr_number}` }]} />

      <div className="card">
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <h1 style={{ margin: 0, fontSize: 20 }}>
            {review.title || `PR #${review.pr_number}`}
          </h1>
          <StatusBadge status={review.status} />
        </div>
        <div className="pr-meta" title={repo?.full_name}>
          {repo ? formatRepoName(repo.full_name) : "Unknown repository"} &middot; PR #{review.pr_number} &middot; by{" "}
          {review.author}
        </div>
        <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <a href={review.html_url} target="_blank" rel="noreferrer" className="btn btn-ghost">
            <Icon name="external" size={14} /> View PR/MR
          </a>
          {review.comment_url && (
            <a href={review.comment_url} target="_blank" rel="noreferrer" className="btn btn-ghost">
              <Icon name="external" size={14} /> View posted comment
            </a>
          )}
        </div>

        <details className="tech-details">
          <summary>
            <Icon name="chevron-right" size={14} /> Technical details
          </summary>
          <dl className="tech-details-body">
            <dt>Commit</dt>
            <dd>{review.commit_sha}</dd>
            <dt>Review ID</dt>
            <dd>{review.id}</dd>
            <dt>Repository ID</dt>
            <dd>{review.repository_id}</dd>
            <dt>Started</dt>
            <dd>{formatDateTime(review.started_at)}</dd>
            <dt>Completed</dt>
            <dd>{review.completed_at ? formatDateTime(review.completed_at) : "—"}</dd>
          </dl>
        </details>
      </div>

      {review.findings.length === 0 ? (
        <div style={{ marginTop: 20 }}>
          <EmptyState icon="check-circle" title="No issues found" description="This review didn't surface any findings." />
        </div>
      ) : (
        <>
          <div className="filter-bar" style={{ marginTop: 24 }}>
            {availableSeverities.map((sev) => (
              <button
                key={sev}
                type="button"
                className="chip"
                aria-pressed={effectiveActive.has(sev)}
                onClick={() => toggleSeverity(sev)}
              >
                {sev}
              </button>
            ))}
          </div>

          {filteredFindings.length === 0 ? (
            <EmptyState icon="search" title="No findings match the selected severities" />
          ) : (
            CATEGORY_ORDER.map((category) => {
              const findings = filteredFindings.filter((f) => f.category === category);
              if (findings.length === 0) return null;
              return (
                <div key={category}>
                  <div className="section-title" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <CategoryBadge category={category} /> {findings.length} finding(s)
                  </div>
                  {findings.map((f) => (
                    <FindingCard key={f.id} finding={f} />
                  ))}
                </div>
              );
            })
          )}
        </>
      )}
    </div>
  );
}
