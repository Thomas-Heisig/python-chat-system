import type { PluginFrontendModule } from "./types";

const pluginModules = import.meta.glob<{
  default: PluginFrontendModule;
}>(
  "../../../plugins/*/frontend/plugin.tsx",
);

export async function loadPluginFrontend(
  pluginId: string,
): Promise<PluginFrontendModule | null> {
  const entry = Object.entries(pluginModules).find(([path]) =>
    path.includes(`/plugins/${pluginId}/frontend/plugin.tsx`),
  );

  if (!entry) {
    return null;
  }

  const [, loadModule] = entry;
  try {
    const module = await loadModule();
    return module.default;
  } catch (e) {
    console.error(`Failed to load plugin ${pluginId}:`, e);
    return null;
  }
}