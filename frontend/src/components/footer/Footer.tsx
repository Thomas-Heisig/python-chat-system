import { useState } from "react";

type FooterProps = {
  modelLoaded: boolean;
  plugins: string[];
  onOpenPlugin: (plugin: string) => void;
};

export function Footer({ modelLoaded, plugins, onOpenPlugin }: FooterProps) {
  const [showExtended, setShowExtended] = useState(false);

  return (
    <footer className="footer">
      <div className="footer__group">
        <span className="status-line">
          <span className="status-dot status-dot--ok" aria-hidden="true" />
          System bereit
        </span>
        <span className="status-line">
          <span className={`status-dot ${modelLoaded ? "status-dot--ok" : "status-dot--error"}`} aria-hidden="true" />
          {modelLoaded ? "Modell geladen" : "Modell fehlt"}
        </span>
        <span className="status-line">
          <span className="status-dot status-dot--ok" aria-hidden="true" />
          Datenbank verbunden
        </span>
        <span className="status-line">
          🔌
          {plugins.map((plugin) => (
            <button key={plugin} type="button" className="ghost-btn" onClick={() => onOpenPlugin(plugin)}>
              {plugin}
            </button>
          ))}
        </span>
      </div>

      <div className="footer__group">
        <span>Queue: 0</span>
        {showExtended ? <span>VRAM: 8,4 / 12 GB</span> : null}
        {showExtended ? <span>Tokens heute: 12.340</span> : null}
        {showExtended ? <span>Worker: 2 / 4</span> : null}
        <span>v0.1.0</span>
        <button type="button" className="ghost-btn" onClick={() => setShowExtended((current) => !current)}>
          {showExtended ? "Standard" : "Details"}
        </button>
      </div>
    </footer>
  );
}
