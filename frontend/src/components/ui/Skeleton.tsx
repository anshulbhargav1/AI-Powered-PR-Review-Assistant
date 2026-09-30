export function SkeletonLine({ width = "100%" }: { width?: string | number }) {
  return <div className="skeleton skeleton-line" style={{ width }} />;
}

export function SkeletonBlock({ height }: { height?: number }) {
  return <div className="skeleton skeleton-block" style={height ? { height } : undefined} />;
}

export function SkeletonStatRow({ count = 4 }: { count?: number }) {
  return (
    <div className="stat-row">
      {Array.from({ length: count }).map((_, i) => (
        <div className="stat-tile" key={i}>
          <SkeletonLine width="60%" />
          <SkeletonLine width="80%" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 6 }: { rows?: number }) {
  return (
    <div className="card">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} style={{ marginBottom: 12 }}>
          <SkeletonLine width="90%" />
        </div>
      ))}
    </div>
  );
}
