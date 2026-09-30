import type { Repository, ReviewRun, ReviewRunDetail, Stats } from "../types";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText} for ${path}`);
  }
  return res.json() as Promise<T>;
}

export interface ListReviewsParams {
  repositoryId?: string;
  limit?: number;
  offset?: number;
}

export const api = {
  listReviews: ({ repositoryId, limit, offset }: ListReviewsParams = {}) => {
    const params = new URLSearchParams();
    if (repositoryId) params.set("repository_id", repositoryId);
    if (limit !== undefined) params.set("limit", String(limit));
    if (offset !== undefined) params.set("offset", String(offset));
    const qs = params.toString();
    return getJSON<ReviewRun[]>(`/api/reviews${qs ? `?${qs}` : ""}`);
  },
  getReview: (id: string) => getJSON<ReviewRunDetail>(`/api/reviews/${id}`),
  listRepos: () => getJSON<Repository[]>(`/api/repos`),
  getStats: () => getJSON<Stats>(`/api/stats`),
};
