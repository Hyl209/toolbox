import type { SettingsSnapshot, ToolItem } from "../../../api/tauri";
import type { SettingsDraftState } from "..";
import { settingsModeText } from "./viewState";

type DerivedSettingsCollectionsArgs = {
  snapshot: SettingsSnapshot | null;
  fallbackTools: readonly ToolItem[];
  drafts: SettingsDraftState;
};

export function deriveSettingsCollections({
  snapshot,
  fallbackTools,
  drafts,
}: DerivedSettingsCollectionsArgs) {
  const allTools = snapshot?.tools ?? fallbackTools;
  const builtinTools = allTools.filter((tool) => tool.source !== "plugin");
  const pluginTools = allTools.filter((tool) => tool.source === "plugin");
  const toolsById = new Map(allTools.map((tool) => [tool.id, tool]));
  const orderedTools = drafts.sidebarOrder.flatMap((toolId) => {
    const tool = toolsById.get(toolId);
    return tool ? [tool] : [];
  });
  const enabledTools = allTools.filter((tool) => {
    if (tool.source === "plugin") {
      return tool.manifest_enabled !== false && !drafts.disabledPlugins.has(tool.plugin_name ?? tool.id.replace(/^plugin:/, ""));
    }
    return !drafts.disabledTools.has(tool.id);
  }).length;
  const modeText = settingsModeText(drafts.theme, drafts.customThemeEnabled);

  return {
    allTools,
    builtinTools,
    pluginTools,
    toolsById,
    orderedTools,
    enabledTools,
    modeText,
  };
}
