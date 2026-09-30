import { Icon } from "./Icon";

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="state-block state-error">
      <div className="state-icon">
        <Icon name="x-circle" size={32} />
      </div>
      <div className="state-title">Something went wrong</div>
      <div className="state-desc">{message}</div>
      {onRetry && (
        <button className="btn" onClick={onRetry} type="button">
          Try again
        </button>
      )}
    </div>
  );
}
