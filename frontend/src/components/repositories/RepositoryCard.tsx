import { Link } from "react-router-dom";
import type { Repository } from "../../types";
import { formatRepoName } from "../../utils/repo";

export function RepositoryCard({ repo }: { repo: Repository }) {
  return (
    <div className="repo-card">
      <span className="badge" style={{ alignSelf: "flex-start", color: "var(--text-secondary)", background: "var(--surface-3)" }}>
        {repo.provider}
      </span>
      <div className="repo-card-name" title={repo.full_name}>
        {formatRepoName(repo.full_name)}
      </div>
      <div className="repo-card-meta" title={repo.full_name}>
        {repo.full_name}
      </div>
      <div className="repo-card-meta">
        {repo.review_run_count} review{repo.review_run_count === 1 ? "" : "s"}
      </div>
      <div className="repo-card-footer">
        <Link to={`/reviews?repository_id=${encodeURIComponent(repo.id)}`} className="btn btn-ghost">
          View reviews
        </Link>
      </div>
    </div>
  );
}
