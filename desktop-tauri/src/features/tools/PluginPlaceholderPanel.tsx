import type { ToolItem } from "../../api/tauri";

type PluginPlaceholderPanelProps = {
  tool: ToolItem;
};

function statusText(tool: ToolItem): string {
  if (tool.manifest_enabled === false) {
    return "manifest 已禁用";
  }
  if (tool.enabled === false) {
    return "已禁用";
  }
  if (tool.status === "pending") {
    return "待接入";
  }
  return "插件 UI 未注册";
}

function bodyText(tool: ToolItem): string {
  if (tool.manifest_enabled === false) {
    return "该插件已在 manifest 中禁用，当前只保留设置与排序记录。";
  }
  if (tool.enabled === false) {
    return "\u8be5\u63d2\u4ef6\u5df2\u7981\u7528\u3002";
  }
  if (tool.status === "pending") {
    return "插件入口已同步，面板待接入。";
  }
  return "插件已识别，面板待注册。";
}

export default function PluginPlaceholderPanel({ tool }: PluginPlaceholderPanelProps) {
  return (
    <div className="empty-tool-panel">
      <h2>{tool.title}</h2>
      <p>{bodyText(tool)}</p>
      <span className="settings-mode-pill">{statusText(tool)}</span>
      <details className="settings-detail-card">
        <summary>插件详情</summary>
        <div className="settings-tool-list">
          {tool.plugin_name ? (
            <div className="settings-control-row">
              <label className="field-block">
                <span>plugin_name</span>
                <input readOnly type="text" value={tool.plugin_name} />
              </label>
              <label className="field-block">
                <span>status</span>
                <input readOnly type="text" value={tool.status} />
              </label>
              <label className="field-block">
                <span>supported_in_tauri</span>
                <input readOnly type="text" value={String(tool.supported_in_tauri)} />
              </label>
            </div>
          ) : null}
          {tool.description ? (
            <label className="field-block">
              <span>description</span>
              <textarea readOnly value={tool.description} />
            </label>
          ) : null}
        </div>
      </details>
    </div>
  );
}
