import type { ToolItem } from "../../../api/tauri";
import { SettingToggleRow } from "./primitives";

type BuiltinToolsSectionProps = {
  builtinTools: ToolItem[];
  disabledTools: Set<string>;
  onToggle: (toolId: string, enabled: boolean) => void;
  toolDisplayName: (tool: ToolItem) => string;
  toolMetadata: (tool: ToolItem) => string[];
};

export function BuiltinToolsSection({
  builtinTools,
  disabledTools,
  onToggle,
  toolDisplayName,
  toolMetadata,
}: BuiltinToolsSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>内置工具</span>
      <p>这里只控制内置工具的显示与默认启用状态。</p>
      <div className="settings-toggle-grid">
        {builtinTools.map((tool) => {
          const enabled = !disabledTools.has(tool.id);
          return (
            <SettingToggleRow
              checked={enabled}
              description={tool.description || tool.title}
              key={tool.id}
              label={toolDisplayName(tool)}
              meta={toolMetadata(tool).join(" · ")}
              onChange={(checked) => onToggle(tool.id, checked)}
            />
          );
        })}
      </div>
    </section>
  );
}

type SidebarOrderSectionProps = {
  orderedTools: ToolItem[];
  saving: boolean;
  disabledTools: Set<string>;
  disabledPlugins: Set<string>;
  onMove: (toolId: string, direction: -1 | 1) => void;
  toolMetadata: (tool: ToolItem) => string[];
  sidebarStatus: (tool: ToolItem, disabledTools: Set<string>, disabledPlugins: Set<string>) => string;
};

export function SidebarOrderSection({
  orderedTools,
  saving,
  disabledTools,
  disabledPlugins,
  onMove,
  toolMetadata,
  sidebarStatus,
}: SidebarOrderSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>侧栏顺序</span>
      <p>排序时保留全部入口，保存后只在侧栏显示启用且 manifest 允许的工具。</p>
      <div className="sidebar-order-list">
        {orderedTools.map((tool, index) => (
          <div className="sidebar-order-row" key={tool.id}>
            <span className="sidebar-order-index">{index + 1}</span>
            <span className="sidebar-order-main">
              <b>{tool.sidebar_label ?? tool.title}</b>
              <small>{[...toolMetadata(tool), sidebarStatus(tool, disabledTools, disabledPlugins)].filter(Boolean).join(" · ")}</small>
            </span>
            <span className="sidebar-order-actions">
              <button disabled={index === 0 || saving} onClick={() => onMove(tool.id, -1)} type="button">
                上移
              </button>
              <button disabled={index === orderedTools.length - 1 || saving} onClick={() => onMove(tool.id, 1)} type="button">
                下移
              </button>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

type PluginStatusSectionProps = {
  pluginTools: ToolItem[];
  disabledPlugins: Set<string>;
  onToggle: (tool: ToolItem, enabled: boolean) => void;
  toolDisplayName: (tool: ToolItem) => string;
  toolMetadata: (tool: ToolItem) => string[];
  pluginConfigKey: (tool: ToolItem) => string;
};

export function PluginStatusSection({
  pluginTools,
  disabledPlugins,
  onToggle,
  toolDisplayName,
  toolMetadata,
  pluginConfigKey,
}: PluginStatusSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>插件状态</span>
      <p>这里回写 `plugins/disabled`；manifest 已禁用的插件无法在此重新启用。</p>
      <div className="settings-toggle-grid">
        {pluginTools.length
          ? pluginTools.map((tool) => {
            const enabled = tool.manifest_enabled !== false && !disabledPlugins.has(pluginConfigKey(tool));
            return (
              <SettingToggleRow
                checked={enabled}
                description={tool.description || tool.title}
                disabled={tool.manifest_enabled === false}
                key={tool.id}
                label={toolDisplayName(tool)}
                meta={[
                  ...toolMetadata(tool),
                  tool.manifest_enabled === false ? "manifest 已禁用" : enabled ? "启用" : "已禁用",
                ].filter(Boolean).join(" · ")}
                onChange={(checked) => onToggle(tool, checked)}
              />
            );
          })
          : <small>暂无插件入口</small>}
      </div>
    </section>
  );
}
