import { useMemo, type CSSProperties, type ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useRepositories } from "../context/RepositoriesContext";
import { useReviews } from "../hooks/useReviews";
import { useStats } from "../hooks/useStats";
import { categoryColor, severityColor, StatusBadge } from "../components/ui/Badges";
import { StatTile } from "../components/ui/StatTile";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { SkeletonStatRow, SkeletonTable } from "../components/ui/Skeleton";
import { formatRelativeTime } from "../utils/time";
import { formatRepoName } from "../utils/repo";
import type { Category, Repository, ReviewRun, Severity } from "../types";

const CATEGORY_ORDER: Category[] = ["security", "performance", "code_quality", "testing"];
const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

const GRID = "var(--grid)";
const MUTED = "var(--text-muted)";

const TOOLTIP_CONTENT_STYLE: CSSProperties = {
  background: "var(--surface-2)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-sm)",
  boxShadow: "var(--shadow-md)",
  padding: "8px 12px",
};
const TOOLTIP_LABEL_STYLE: CSSProperties = { color: "var(--text-primary)" };
const TOOLTIP_ITEM_STYLE: CSSProperties = { color: "var(--text-secondary)" };

function attentionScore(r: ReviewRun): number {
  return (r.by_severity.critical ?? 0) * 100 + (r.by_severity.high ?? 0) * 10 + (r.by_severity.medium ?? 0);
}

function ReviewWidgetRow({
  review,
  repo,
  right,
}: {
  review: ReviewRun;
  repo: Repository | undefined;
  right: ReactNode;
}) {
  return (
    <div className="widget-row">
      <div className="widget-row-main">
        <div className="widget-row-title">
          <Link to={`/reviews/${review.id}`}>{review.title || `PR #${review.pr_number}`}</Link>
        </div>
        <div className="widget-row-meta" title={repo?.full_name}>
          {repo ? formatRepoName(repo.full_name) : "Unknown repository"} &middot; {formatRelativeTime(review.started_at)}
        </div>
      </div>
      {right}
    </div>
  );
}

export function Dashboard() {
  const { stats, error: statsError, reload: reloadStats } = useStats();
  const { reviews, error: reviewsError, reload: reloadReviews } = useReviews();
  const { repoById, repos } = useRepositories();

  const needsAttention = useMemo(() => {
    if (!reviews) return [];
    return [...reviews].filter((r) => attentionScore(r) > 0).sort((a, b) => attentionScore(b) - attentionScore(a)).slice(0, 5);
  }, [reviews]);

  const recent = useMemo(() => (reviews ? reviews.slice(0, 5) : []), [reviews]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <div className="page-subtitle">Overview of AI code reviews across your connected repositories.</div>
        </div>
      </div>

      {statsError ? (
        <ErrorState message={statsError} onRetry={reloadStats} />
      ) : stats === null ? (
        <SkeletonStatRow count={5} />
      ) : (
        <div className="stat-row">
          <StatTile label="Total reviews" value={stats.total_reviews} />
          <StatTile label="Total findings" value={stats.total_findings} />
          <StatTile
            label="Avg findings / review"
            value={stats.total_reviews ? (stats.total_findings / stats.total_reviews).toFixed(1) : "0"}
          />
          <StatTile label="Critical findings" value={stats.by_severity["critical"] || 0} />
          <StatTile label="Repositories" value={repos.length} />
        </div>
      )}

      {stats && stats.total_reviews > 0 && (
        <div className="chart-grid">
          <div className="card">
            <div className="chart-title">Findings by category</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={CATEGORY_ORDER.map((c) => ({ name: c, count: stats.by_category[c] || 0 }))} barCategoryGap="30%">
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis dataKey="name" tick={{ fill: MUTED, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip
                  cursor={{ fill: "rgba(128,128,128,0.08)" }}
                  contentStyle={TOOLTIP_CONTENT_STYLE}
                  labelStyle={TOOLTIP_LABEL_STYLE}
                  itemStyle={TOOLTIP_ITEM_STYLE}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
                  {CATEGORY_ORDER.map((c) => (
                    <Cell key={c} fill={categoryColor(c)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="chart-title">Findings by severity</div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={SEVERITY_ORDER.map((s) => ({ name: s, count: stats.by_severity[s] || 0 }))} barCategoryGap="30%">
                <CartesianGrid stroke={GRID} vertical={false} />
                <XAxis dataKey="name" tick={{ fill: MUTED, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} width={28} />
                <Tooltip
                  cursor={{ fill: "rgba(128,128,128,0.08)" }}
                  contentStyle={TOOLTIP_CONTENT_STYLE}
                  labelStyle={TOOLTIP_LABEL_STYLE}
                  itemStyle={TOOLTIP_ITEM_STYLE}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={48}>
                  {SEVERITY_ORDER.map((s) => (
                    <Cell key={s} fill={severityColor(s)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {stats && stats.total_reviews > 0 && (
        <div className="card" style={{ marginTop: 20 }}>
          <div className="chart-title">Reviews per day (last 14 days with activity)</div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={Object.entries(stats.recent_reviews_per_day).map(([date, count]) => ({ date, count }))}>
              <CartesianGrid stroke={GRID} vertical={false} />
              <XAxis dataKey="date" tick={{ fill: MUTED, fontSize: 12 }} axisLine={{ stroke: GRID }} tickLine={false} />
              <YAxis allowDecimals={false} tick={{ fill: MUTED, fontSize: 12 }} axisLine={false} tickLine={false} width={28} />
              <Tooltip
                contentStyle={TOOLTIP_CONTENT_STYLE}
                labelStyle={TOOLTIP_LABEL_STYLE}
                itemStyle={TOOLTIP_ITEM_STYLE}
              />
              <Line type="monotone" dataKey="count" stroke="var(--cat-security)" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="two-col" style={{ marginTop: 8 }}>
        <div>
          <div className="section-title">Needs attention</div>
          <div className="card">
            {reviewsError ? (
              <ErrorState message={reviewsError} onRetry={reloadReviews} />
            ) : reviews === null ? (
              <SkeletonTable rows={3} />
            ) : needsAttention.length === 0 ? (
              <EmptyState icon="check-circle" title="Nothing urgent" description="No reviews currently have critical or high severity findings." />
            ) : (
              <div className="widget-list">
                {needsAttention.map((r) => (
                  <ReviewWidgetRow
                    key={r.id}
                    review={r}
                    repo={repoById(r.repository_id)}
                    right={
                      <div className="badge-group">
                        {SEVERITY_ORDER.filter((s) => r.by_severity[s]).slice(0, 2).map((s) => (
                          <span key={s} className="badge" style={{ color: severityColor(s), background: `color-mix(in srgb, ${severityColor(s)} 16%, transparent)` }}>
                            {r.by_severity[s]} {s}
                          </span>
                        ))}
                      </div>
                    }
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <div className="section-title">Recent activity</div>
          <div className="card">
            {reviewsError ? (
              <ErrorState message={reviewsError} onRetry={reloadReviews} />
            ) : reviews === null ? (
              <SkeletonTable rows={3} />
            ) : recent.length === 0 ? (
              <EmptyState
                icon="reviews"
                title="No reviews yet"
                description="Open a PR/MR on a connected repository to trigger a review."
              />
            ) : (
              <div className="widget-list">
                {recent.map((r) => (
                  <ReviewWidgetRow
                    key={r.id}
                    review={r}
                    repo={repoById(r.repository_id)}
                    right={<StatusBadge status={r.status} />}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
