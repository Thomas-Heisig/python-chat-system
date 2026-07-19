# Plugin Documentation Index

Diese Seite ist der Einstiegspunkt fuer alle, die Plugins entwickeln, erweitern oder integrieren.

## Empfohlene Lesereihenfolge

1. [Plugin System Architecture](../architecture/plugin-system.md)
   - Gesamtbild, Rollen und stabile Architekturgrenzen.

2. [Plugin Development Guide](plugin-development.md)
   - Pflichtbestandteile eines Plugins und der Standard-Workflow.

3. [Plugin Standards](standards.md)
   - Metadaten-, Schema- und Kompatibilitaetsregeln.

4. [Dynamic Plugin Settings](settings.md)
   - Zentrale Regeln fuer `PLUGIN_META.settingsFields` und generisches Frontend-Rendering.

5. [Plugin Validation Guidelines](validation.md)
   - Einheitliches Validierungsmodell und Status-Logik.

6. [Communication Plugin Conventions](communication.md)
   - Spezifische Konventionen fuer Brief-/E-Mail-orientierte Plugins.

## Schnellnavigation nach Ziel

- Neues Plugin erstellen:
  1) [plugin-development.md](plugin-development.md)
  2) [standards.md](standards.md)
  3) [settings.md](settings.md)

- Frontend-Integration fuer Plugin-Settings:
  1) [settings.md](settings.md)
  2) [plugin-system.md](../architecture/plugin-system.md)

- Validierungs-/Statusfragen:
  1) [validation.md](validation.md)
  2) [communication.md](communication.md)

## Abgrenzung

- Plugin-spezifische Details (Inputs, Beispiele, Besonderheiten) bleiben in der jeweiligen Plugin-README.
- Systemweite Regeln und Querschnittsstandards liegen zentral in `docs/plugins/` und `docs/architecture/`.
