import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ReviewRun } from "../types";

const PAGE_SIZE = 25;

export function useReviews(repositoryId?: string) {
  const [reviews, setReviews] = useState<ReviewRun[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setReviews(null);
    setError(null);
    api
      .listReviews({ repositoryId, limit: PAGE_SIZE, offset: 0 })
      .then((data) => {
        if (cancelled) return;
        setReviews(data);
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [repositoryId, reloadToken]);

  const loadMore = useCallback(() => {
    setLoadingMore(true);
    api
      .listReviews({ repositoryId, limit: PAGE_SIZE, offset: reviews?.length ?? 0 })
      .then((data) => {
        setReviews((prev) => [...(prev ?? []), ...data]);
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoadingMore(false));
  }, [repositoryId, reviews?.length]);

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  return { reviews, error, hasMore, loadingMore, loadMore, reload };
}
