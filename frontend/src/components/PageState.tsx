import { AlertCircle, Inbox, LoaderCircle, RefreshCw } from "lucide-react";

import { useDemo } from "../context/DemoContext";


export function LoadingState() {
  const { t } = useDemo();
  return (
    <div className="page-state" role="status" aria-live="polite">
      <LoaderCircle className="spin" aria-hidden="true" />
      <p>{t("loading")}</p>
    </div>
  );
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const { t } = useDemo();
  return (
    <div className="page-state page-state-error" role="alert">
      <AlertCircle aria-hidden="true" />
      <div>
        <strong>{t("backendUnavailable")}</strong>
        <p>{error.message}</p>
      </div>
      <button className="button button-secondary" type="button" onClick={onRetry}>
        <RefreshCw size={16} aria-hidden="true" />
        {t("retry")}
      </button>
    </div>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="page-state page-state-empty">
      <Inbox aria-hidden="true" />
      <strong>{title}</strong>
      {description ? <p>{description}</p> : null}
    </div>
  );
}
