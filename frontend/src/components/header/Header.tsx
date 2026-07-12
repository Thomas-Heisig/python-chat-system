import { useEffect, useState } from "react";

type HeaderProps = {
  onOpenLeftMenu: () => void;
  modelLoaded: boolean;
  onOpenSettings: () => void;
  selectedProjectName: string;
  onOpenProjects: () => void;
  locale: string;
  timezone: string;
  language: "de" | "en";
};

function formatNow(now: Date, locale: string, timezone: string): { dateLabel: string; timeLabel: string } {
  return {
    dateLabel: now.toLocaleDateString(locale, {
      weekday: "short",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      timeZone: timezone,
    }),
    timeLabel: now.toLocaleTimeString(locale, {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: timezone,
    }),
  };
}

export function Header({ onOpenLeftMenu, modelLoaded, onOpenSettings, selectedProjectName, onOpenProjects, locale, timezone, language }: HeaderProps) {
  const [clock, setClock] = useState(() => formatNow(new Date(), locale, timezone));

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setClock(formatNow(new Date(), locale, timezone));
    }, 60_000);

    return () => window.clearInterval(intervalId);
  }, [locale, timezone]);

  const ui = language === "en"
    ? {
        openNav: "Open navigation",
        project: "Project",
        modelReady: "Model ready",
        modelNotLoaded: "Model not loaded",
        settings: "Settings",
      }
    : {
        openNav: "Navigation oeffnen",
        project: "Projekt",
        modelReady: "Modell bereit",
        modelNotLoaded: "Modell nicht geladen",
        settings: "Einstellungen",
      };

  return (
    <header className="header">
      <div className="header__left">
        <button type="button" className="icon-btn mobile-menu-btn" onClick={onOpenLeftMenu} aria-label={ui.openNav}>
          ☰
        </button>
        <strong className="brand">Local Chat</strong>
        <button type="button" className="project-chip" onClick={onOpenProjects}>
          {ui.project}: {selectedProjectName}
        </button>
      </div>

      <div className="header__right">
        <span className="status-chip">
          <span className={`status-dot ${modelLoaded ? "status-dot--ok" : "status-dot--error"}`} aria-hidden="true" />
          {modelLoaded ? ui.modelReady : ui.modelNotLoaded}
        </span>

        <span className="clock">
          <div>{clock.dateLabel}</div>
          <div>{clock.timeLabel}</div>
        </span>

        <button type="button" className="icon-btn" onClick={onOpenSettings} aria-label={ui.settings}>
          ⚙
        </button>
      </div>
    </header>
  );
}
