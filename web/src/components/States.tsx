import type { ReactNode } from 'react';

export function LoadingState({ label = 'Loading data…' }: { label?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p style={{ margin: 0 }}>{label}</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state" role="alert">
      <p className="state__title">Something went wrong</p>
      <p style={{ margin: 0 }}>{message}</p>
      <p className="small" style={{ margin: 0 }}>
        Try refreshing. If the problem persists the published data may still be generating.
      </p>
    </div>
  );
}

export function EmptyState({
  title = 'Nothing to show',
  children,
}: {
  title?: string;
  children?: ReactNode;
}) {
  return (
    <div className="state">
      <p className="state__title">{title}</p>
      {children && <p style={{ margin: 0 }}>{children}</p>}
    </div>
  );
}
