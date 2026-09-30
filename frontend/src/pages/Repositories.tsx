import { useRepositories } from "../context/RepositoriesContext";
import { RepositoryCard } from "../components/repositories/RepositoryCard";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { SkeletonBlock } from "../components/ui/Skeleton";

export function Repositories() {
  const { repos, loading, error } = useRepositories();

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Repositories</h1>
          <div className="page-subtitle">Repositories connected to TIRA for automated PR/MR review.</div>
        </div>
      </div>

      {error ? (
        <ErrorState message={error} />
      ) : loading ? (
        <div className="repo-grid">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonBlock key={i} height={120} />
          ))}
        </div>
      ) : repos.length === 0 ? (
        <EmptyState
          icon="repositories"
          title="No repositories connected"
          description="Connect a repository via the webhook gateway to start receiving automated reviews."
        />
      ) : (
        <div className="repo-grid">
          {repos.map((repo) => (
            <RepositoryCard key={repo.id} repo={repo} />
          ))}
        </div>
      )}
    </div>
  );
}
