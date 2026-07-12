export type ToastItem = {
  id: string;
  tone: "success" | "info" | "error";
  message: string;
  sticky: boolean;
};

type ToastHostProps = {
  items: ToastItem[];
  onClose: (id: string) => void;
};

export function ToastHost({ items, onClose }: ToastHostProps) {
  return (
    <div className="toast-host" aria-live="polite" aria-atomic="true">
      {items.map((toast) => (
        <article key={toast.id} className={`toast toast--${toast.tone}`}>
          {toast.tone === "error" ? (
            <span role="alert">{toast.message}</span>
          ) : (
            <span role="status">{toast.message}</span>
          )}
          <button type="button" className="icon-btn" aria-label="Meldung schliessen" onClick={() => onClose(toast.id)}>
            ✕
          </button>
        </article>
      ))}
    </div>
  );
}
