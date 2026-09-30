import { useSearchParams } from "react-router-dom";
import { useRepositories } from "../context/RepositoriesContext";
import { useReviews } from "../hooks/useReviews";
import { ReviewsTable } from "../components/reviews/ReviewsTable";
import { ErrorState } from "../components/ui/ErrorState";
import { EmptyState } from "../components/ui/EmptyState";
import { SkeletonTable } from "../components/ui/Skeleton";
import { formatRepoName } from "../utils/repo";

export function Reviews() {
  const [searchParams, setSearchParams] = useSearchParams();
  const repositoryId = searchParams.get("repository_id") ?? "";
  const { repos, repoById } = useRepositories();
  const { reviews, error, hasMore, loadingMore, loadMore, reload } = useReviews(repositoryId || undefined);

  const handleRepositoryChange = (id: string) => {
    if (id) {
      setSearchParams({ repository_id: id });
    } else {
      setSearchParams({});
    }
  };

  const selectedRepo = repositoryId ? repoById(repositoryId) : undefined;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Reviews</h1>
          <div className="page-subtitle">
            {selectedRepo ? `Reviews for ${formatRepoName(selectedRepo.full_name)}` : "All AI-generated pull request and merge request reviews."}
          </div>
        </div>
      </div>

      {error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : reviews === null ? (
        <SkeletonTable rows={8} />
      ) : reviews.length === 0 && !repositoryId ? (
        <EmptyState
          icon="reviews"
          title="No reviews yet"
          description={
            <>
              Open a PR/MR on a connected repository, or run <code>scripts/simulate_webhook.py</code> to trigger
              one locally.
            </>
          }
        />
      ) : (
        <ReviewsTable
          reviews={reviews}
          repoById={repoById}
          repos={repos}
          selectedRepositoryId={repositoryId}
          onRepositoryChange={handleRepositoryChange}
          hasMore={hasMore}
          loadingMore={loadingMore}
          onLoadMore={loadMore}
        />
      )}
    </div>
  );
}
