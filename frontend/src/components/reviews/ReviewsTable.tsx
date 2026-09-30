import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { SeverityBadge, StatusBadge } from "../ui/Badges";
import { EmptyState } from "../ui/EmptyState";
import { Icon } from "../ui/Icon";
import type { Repository, ReviewRun, Severity } from "../../types";
import { formatDateTime, formatRelativeTime } from "../../utils/time";
import { formatRepoName } from "../../utils/repo";

const SEVERITY_ORDER: Severity[] = ["critical", "high", "medium", "low", "info"];

type SortKey = "started_at" | "total_findings";

function FindingsSummary({ bySeverity, total }: { bySeverity: Record<string, number>; total: number }) {
  if (total === 0) {
    return <span style={{ color: "var(--text-muted)", fontSize: 13 }}>No findings</span>;
  }
  const present = SEVERITY_ORDER.filter((s) => bySeverity[s]);
  return (
    <div className="badge-group">
      {present.slice(0, 3).map((sev) => (
        <SeverityBadge key={sev} severity={sev} />
      ))}
    </div>
  );
}

export function ReviewsTable({
  reviews,
  repoById,
  repos,
  selectedRepositoryId,
  onRepositoryChange,
  hasMore,
  loadingMore,
  onLoadMore,
}: {
  reviews: ReviewRun[];
  repoById: (id: string) => Repository | undefined;
  repos: Repository[];
  selectedRepositoryId: string;
  onRepositoryChange: (id: string) => void;
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
}) {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("started_at");
  const [sortDesc, setSortDesc] = useState(true);

  const statuses = useMemo(() => Array.from(new Set(reviews.map((r) => r.status))).sort(), [reviews]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let result = reviews.filter((r) => {
      if (statusFilter !== "all" && r.status !== statusFilter) return false;
      if (!q) return true;
      const repoName = repoById(r.repository_id)?.full_name ?? "";
      return (
        r.title.toLowerCase().includes(q) ||
        r.author.toLowerCase().includes(q) ||
        repoName.toLowerCase().includes(q) ||
        String(r.pr_number).includes(q)
      );
    });
    result = [...result].sort((a, b) => {
      const dir = sortDesc ? -1 : 1;
      if (sortKey === "total_findings") return dir * (a.total_findings - b.total_findings);
      return dir * (new Date(a.started_at).getTime() - new Date(b.started_at).getTime());
    });
    return result;
  }, [reviews, search, statusFilter, sortKey, sortDesc, repoById]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDesc((d) => !d);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  };

  return (
    <div>
      <div className="filter-bar">
        <div className="search-field">
          <span className="search-field-icon">
            <Icon name="search" size={15} />
          </span>
          <input
            type="search"
            className="input"
            placeholder="Search by title, author, or repository"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search reviews"
          />
        </div>
        <select
          className="select"
          value={selectedRepositoryId}
          onChange={(e) => onRepositoryChange(e.target.value)}
          aria-label="Filter by repository"
        >
          <option value="">All repositories</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>
              {formatRepoName(r.full_name)}
            </option>
          ))}
        </select>
        <select
          className="select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Filter by status"
        >
          <option value="all">All statuses</option>
          {statuses.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          icon="search"
          title="No reviews match your filters"
          description="Try clearing the search or filters above."
        />
      ) : (
        <>
          <div className="table-wrap">
            <table className="responsive-table">
              <thead>
                <tr>
                  <th>Review</th>
                  <th>Author</th>
                  <th>Findings</th>
                  <th>Status</th>
                  <th>
                    <button
                      type="button"
                      className="sort-btn"
                      onClick={() => toggleSort("started_at")}
                      aria-label={`Sort by started date, currently ${sortKey === "started_at" ? (sortDesc ? "descending" : "ascending") : "not sorted"}`}
                    >
                      Started
                      {sortKey === "started_at" && <Icon name={sortDesc ? "chevron-down" : "chevron-up"} size={13} />}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => {
                  const repo = repoById(r.repository_id);
                  return (
                    <tr
                      key={r.id}
                      className="row-link"
                      onClick={() => navigate(`/reviews/${r.id}`)}
                    >
                      <td data-label="Review" className="review-title-cell">
                        <Link to={`/reviews/${r.id}`} onClick={(e) => e.stopPropagation()}>
                          {r.title || `PR #${r.pr_number}`}
                        </Link>
                        <div className="pr-meta" title={repo?.full_name}>
                          {repo ? formatRepoName(repo.full_name) : "Unknown repository"} &middot; #{r.pr_number}
                        </div>
                      </td>
                      <td data-label="Author">{r.author}</td>
                      <td data-label="Findings">
                        <FindingsSummary bySeverity={r.by_severity} total={r.total_findings} />
                      </td>
                      <td data-label="Status">
                        <StatusBadge status={r.status} />
                      </td>
                      <td data-label="Started" title={formatDateTime(r.started_at)}>
                        {formatRelativeTime(r.started_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {hasMore && (
            <div className="load-more-row">
              <button type="button" className="btn" onClick={onLoadMore} disabled={loadingMore}>
                {loadingMore ? "Loading…" : "Load more"}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
