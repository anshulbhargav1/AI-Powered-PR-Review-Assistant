import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ReviewRunDetail } from "../types";

export function useReview(id: string | undefined) {
  const [review, setReview] = useState<ReviewRunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setReview(null);
    setError(null);
    api
      .getReview(id)
      .then((data) => {
        if (!cancelled) setReview(data);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [id, reloadToken]);

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  return { review, error, reload };
}
