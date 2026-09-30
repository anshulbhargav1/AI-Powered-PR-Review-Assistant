import type { Category, Severity } from "../../types";
import { Icon } from "./Icon";

const SEVERITY_VAR: Record<Severity, string> = {
  critical: "var(--sev-critical)",
  high: "var(--sev-high)",
  medium: "var(--sev-medium)",
  low: "var(--sev-low)",
  info: "var(--sev-info)",
};

const CATEGORY_VAR: Record<Category, string> = {
  security: "var(--cat-security)",
  performance: "var(--cat-performance)",
  code_quality: "var(--cat-code-quality)",
  testing: "var(--cat-testing)",
};

const CATEGORY_LABEL: Record<Category, string> = {
  security: "security",
  performance: "performance",
  code_quality: "code quality",
  testing: "testing",
};

export function severityColor(severity: Severity): string {
  return SEVERITY_VAR[severity] ?? "var(--sev-info)";
}

export function categoryColor(category: Category): string {
  return CATEGORY_VAR[category] ?? "var(--text-muted)";
}

function ColorBadge({ color, label }: { color: string; label: string }) {
  return (
    <span className="badge" style={{ color, background: `color-mix(in srgb, ${color} 16%, transparent)` }}>
      <span className="badge-dot" style={{ background: color }} />
      {label}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return <ColorBadge color={severityColor(severity)} label={severity} />;
}

export function CategoryBadge({ category }: { category: Category }) {
  return <ColorBadge color={categoryColor(category)} label={CATEGORY_LABEL[category] ?? category} />;
}

const STATUS_META: Record<string, { color: string; icon: "check-circle" | "loader" | "alert" }> = {
  completed: { color: "var(--sev-low)", icon: "check-circle" },
  running: { color: "var(--cat-security)", icon: "loader" },
};

export function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_META[status] ?? { color: "var(--text-muted)", icon: "alert" as const };
  return (
    <span
      className="badge"
      style={{ color: meta.color, background: `color-mix(in srgb, ${meta.color} 16%, transparent)` }}
    >
      <Icon name={meta.icon} size={12} />
      {status}
    </span>
  );
}
