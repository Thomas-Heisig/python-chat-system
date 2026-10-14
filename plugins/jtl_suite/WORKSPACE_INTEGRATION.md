# Workspace-Integration

Die exakten Namen der vorhandenen Workspace-Props können im Projekt abweichen. Die Einbindung entspricht dem Muster des `business_letter`-Plugins.

## Import

```tsx
import { JTLSuitePage } from '../../plugins/jtl_suite/frontend/JTLSuitePage';
```

Der relative Pfad muss an den tatsächlichen Speicherort der `WorkspacePage.tsx` angepasst werden.

## Render-Zweig

In dem Bereich, in dem auch `BusinessLetterManualPage` gerendert wird:

```tsx
if (selectedPlugin?.id === 'jtl_suite') {
  return (
    <JTLSuitePage
      currentUserId={currentUser?.id}
      executePlugin={executePlugin}
      pluginMeta={selectedPlugin}
      onClose={closePlugin}
      onOpenSettings={() => setActivePluginTab?.('settings')}
    />
  );
}
```

Falls die Workspace-Komponente keinen `setActivePluginTab`-Callback besitzt, kann `onOpenSettings` zunächst weggelassen oder mit der bereits vorhandenen Settings-Navigation verbunden werden.

## Alte Standalone-Dateien entfernen

Diese Dateien sind für die zentrale Einbindung nicht mehr erforderlich:

```text
plugins/jtl_suite/frontend/index.html
plugins/jtl_suite/frontend/index.ts
plugins/jtl_suite/frontend/package.json
plugins/jtl_suite/frontend/package-lock.json
plugins/jtl_suite/frontend/vite.config.js
```
