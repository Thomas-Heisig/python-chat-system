import type { ComponentType } from "react";

export type PluginInput = Record<string, unknown>;

export type PluginExecutionResult = unknown;

/**
 * Zentrale Signatur zum Ausführen eines Plugins.
 *
 * Falls deine vorhandene executePlugin-Funktion eine andere Signatur hat,
 * muss nur dieser Typ entsprechend angepasst werden.
 */
export type ExecutePlugin = (
  pluginId: string,
  input: PluginInput,
  currentUserId?: string,
) => Promise<PluginExecutionResult>;

/**
 * Gemeinsame Props für alle manuellen Plugin-Seiten.
 *
 * Jede Plugin-Seite muss diesen Props-Vertrag akzeptieren.
 * Nicht benötigte Props können von einer Plugin-Seite ignoriert werden.
 */
export type PluginManualPageProps = {
  pluginId: string;
  currentUserId: string;
  executePlugin: ExecutePlugin;
};

/**
 * Frontend-Definition eines Plugins.
 */
export type PluginFrontendModule = {
  /**
   * Eindeutige Plugin-ID.
   *
   * Muss mit der Plugin-ID des Backends übereinstimmen.
   */
  id: string;

  /**
   * Optionaler Anzeigename.
   */
  name?: string;

  /**
   * Optionale Beschreibung.
   */
  description?: string;

  /**
   * Manuelle Bedienoberfläche des Plugins.
   */
  ManualPage?: ComponentType<PluginManualPageProps>;

  /**
   * Standard-Eingabedaten des Plugins.
   */
  defaultInput?: PluginInput;
};