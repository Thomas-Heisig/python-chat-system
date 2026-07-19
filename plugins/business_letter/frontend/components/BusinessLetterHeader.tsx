import businessLetterLogo from "../../assets/logo.svg";

type BusinessLetterHeaderProps = {
  onClose?: () => void;
};

export function BusinessLetterHeader({ onClose }: BusinessLetterHeaderProps) {
  return (
    <header className="business-letter-header">
      <div className="business-letter-branding">
        <img
          src={businessLetterLogo}
          alt="Business Letter Logo"
          className="business-letter-logo"
          loading="lazy"
        />
        <div>
          <p className="business-letter-eyebrow">Business Letter</p>
          <h1>Geschäftsdokument erstellen</h1>
          <p>Dokument manuell erfassen, prüfen und über das Plugin erzeugen.</p>
        </div>
      </div>
      {onClose ? (
        <button className="bl-button bl-button-secondary" type="button" onClick={onClose}>
          Schließen
        </button>
      ) : null}
    </header>
  );
}
