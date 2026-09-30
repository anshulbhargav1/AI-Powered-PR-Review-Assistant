import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { Repository } from "../types";

interface RepositoriesContextValue {
  repos: Repository[];
  loading: boolean;
  error: string | null;
  repoById: (id: string) => Repository | undefined;
}

const RepositoriesContext = createContext<RepositoriesContextValue | null>(null);

export function RepositoriesProvider({ children }: { children: ReactNode }) {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listRepos()
      .then((data) => setRepos(data))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<RepositoriesContextValue>(() => {
    const byId = new Map(repos.map((r) => [r.id, r]));
    return {
      repos,
      loading,
      error,
      repoById: (id: string) => byId.get(id),
    };
  }, [repos, loading, error]);

  return <RepositoriesContext.Provider value={value}>{children}</RepositoriesContext.Provider>;
}

export function useRepositories() {
  const ctx = useContext(RepositoriesContext);
  if (!ctx) throw new Error("useRepositories must be used within RepositoriesProvider");
  return ctx;
}
