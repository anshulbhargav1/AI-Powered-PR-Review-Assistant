export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Category = "security" | "performance" | "code_quality" | "testing";

export interface Finding {
  id: string;
  category: Category;
  severity: Severity;
  file: string;
  line_number: number | null;
  issue: string;
  explanation: string | null;
  impact: string | null;
  recommendation: string;
  confidence: number;
  agent: string;
}

export interface ReviewRun {
  id: string;
  repository_id: string;
  pr_number: number;
  commit_sha: string;
  title: string;
  author: string;
  html_url: string;
  status: string;
  total_findings: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  comment_url: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface ReviewRunDetail extends ReviewRun {
  findings: Finding[];
}

export interface Repository {
  id: string;
  provider: string;
  full_name: string;
  review_run_count: number;
}

export interface Stats {
  total_reviews: number;
  total_findings: number;
  by_category: Record<string, number>;
  by_severity: Record<string, number>;
  recent_reviews_per_day: Record<string, number>;
}
