import type { ReactNode } from "react";
import type { SettingsSnapshot, ToolItem } from "../../api/tauri";
import toolManifest from "../../tools/manifest";
import { ToolErrorBoundary } from "./components/ToolErrorBoundary";
import PluginPlaceholderPanel from "./PluginPlaceholderPanel";
import { builtinPanelRenderers, pluginPanelRenderers } from "./panels";

export const fallbackTools: ToolItem[] = toolManifest.map((tool) => ({ ...tool, enabled: true, source: "builtin" }));

export const CAPABILITY_NOTES: Record<string, string> = {
  tgdownloader: "部分可用 · 下载/登录",
  webvideodownloader: "部分可用 · 下载/预检",
  directdownloader: "已接入 · 缺 aria2 时仅预览命令",
};

export function isSidebarVisibleTool(tool: ToolItem): boolean {
  if (tool.source === "plugin") {
    return tool.manifest_enabled !== false && tool.enabled !== false;
  }
  return tool.enabled !== false;
}

function mergeSidebarCategories(tools: readonly ToolItem[]): ToolItem[] {
  const grouped = new Map<string, ToolItem[]>();
  const categoryOrder: string[] = [];

  tools.forEach((tool) => {
    if (!grouped.has(tool.category)) {
      grouped.set(tool.category, []);
      categoryOrder.push(tool.category);
    }
    grouped.get(tool.category)?.push(tool);
  });

  return categoryOrder.flatMap((category) => grouped.get(category) ?? []);
}

export function sidebarToolsFromSnapshot(tools: readonly ToolItem[]): ToolItem[] {
  const visible = tools.filter(isSidebarVisibleTool);
  const source = visible.length ? visible : tools;
  return mergeSidebarCategories(source);
}

function emptyStateCopy(tool: ToolItem) {
  if (tool.source === "plugin" && tool.manifest_enabled === false) {
    return {
      eyebrow: "manifest 已禁用",
      body: "该插件已在 manifest 中禁用，当前只保留记录，不在新 UI 中启用。",
    };
  }
  if (tool.enabled === false) {
    return {
      eyebrow: "已禁用",
      body: "\u8be5\u5165\u53e3\u5df2\u7981\u7528\u3002",
    };
  }
  if (tool.status === "pending") {
    return {
      eyebrow: "待接入",
      body: "\u5165\u53e3\u5df2\u540c\u6b65\uff0c\u9762\u677f\u5f85\u63a5\u5165\u3002",
    };
  }
  return {
    eyebrow: "暂未接入",
    body: "当前先保留入口，方便后续平滑迁移。",
  };
}

function renderBuiltinPlaceholder(tool: ToolItem): ReactNode {
  const emptyState = emptyStateCopy(tool);
  return (
    <div className="empty-tool-panel">
      <div className="empty-orb" aria-hidden="true" />
      <p className="eyebrow">{emptyState.eyebrow}</p>
      <h2>{tool.title}</h2>
      <p>{emptyState.body}</p>
    </div>
  );
}

export function renderToolPanel(activeTool: ToolItem, snapshot: SettingsSnapshot | null): ReactNode {
  if (activeTool.source === "plugin") {
    return pluginPanelRenderers[activeTool.id]?.(snapshot) ?? <PluginPlaceholderPanel tool={activeTool} />;
  }
  return builtinPanelRenderers[activeTool.id]?.(snapshot) ?? renderBuiltinPlaceholder(activeTool);
}

export function renderKeepAliveToolPanels(
  tools: readonly ToolItem[],
  activeToolId: string,
  visitedToolIds: readonly string[],
  snapshot: SettingsSnapshot | null,
): ReactNode {
  const visited = new Set([...visitedToolIds, activeToolId]);
  return (
    <>
      {tools
        .filter((tool) => visited.has(tool.id))
        .map((tool) => (
          <section
            aria-hidden={tool.id !== activeToolId}
            className="keep-alive-tool-panel"
            hidden={tool.id !== activeToolId}
            key={tool.id}
          >
            <ToolErrorBoundary>
              {renderToolPanel(tool, snapshot)}
            </ToolErrorBoundary>
          </section>
        ))}
    </>
  );
}
