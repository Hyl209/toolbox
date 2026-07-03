import { getCurrentWindow } from "@tauri-apps/api/window";
import { Fragment, useState, type ReactNode } from "react";
import type { SettingsSnapshot, ToolActivityState, ToolItem } from "../api/tauri";
import { CAPABILITY_NOTES } from "../features/tools";
import { ToolErrorBoundary } from "../features/tools/components/ToolErrorBoundary";
import SupportPopup from "./SupportPopup";
import UserMenu from "./UserMenu";

type ToolShellProps = {
  title: string;
  tools: readonly ToolItem[];
  toolActivity: Record<string, ToolActivityState>;
  activeToolId: string;
  snapshot?: SettingsSnapshot | null;
  lastUser?: string;
  supportImage?: string;
  onLogout?: () => void;
  onOpenSupport?: () => void;
  onSelectTool: (toolId: string) => void;
  onOpenSettings: () => void;
  settingsOpen: boolean;
  children: ReactNode;
};

const categoryLabels: Record<string, string> = {
  audio: "音频",
  document: "文档",
  download: "下载",
  file: "文件",
  image: "图片",
  plugin: "插件",
  text: "文本",
};

const windowActions = {
  close: () => getCurrentWindow().close(),
  maximize: () => getCurrentWindow().toggleMaximize(),
  minimize: () => getCurrentWindow().minimize(),
};

function assertNever(value: never): never {
  throw new Error(`Unhandled tool status: ${String(value)}`);
}

function statusLabel(status: ToolItem["status"]): string {
  switch (status) {
    case "planned":
      return "计划中";
    case "pending":
      return "暂未接入";
    case "ready":
      return "已接入入口";
    default:
      return assertNever(status);
  }
}

function runWindowAction(action: keyof typeof windowActions) {
  if (!("__TAURI_INTERNALS__" in window)) {
    return;
  }
  void windowActions[action]();
}

function toolStatusText(tool: ToolItem): string {
  if (tool.enabled === false) {
    return "已禁用";
  }
  const statusText = CAPABILITY_NOTES[tool.id] ?? statusLabel(tool.status);
  if (tool.source === "plugin") {
    return `${statusText} · 插件`;
  }
  return statusText;
}

function toolTitle(tool: ToolItem | undefined, settingsOpen: boolean): string {
  if (settingsOpen) {
    return "设置";
  }
  return tool?.sidebar_label ?? tool?.title ?? "工具";
}

function ToolShell({
  tools,
  toolActivity,
  activeToolId,
  snapshot,
  lastUser: explicitLastUser,
  supportImage = "",
  onLogout = () => undefined,
  onOpenSupport,
  onSelectTool,
  onOpenSettings,
  settingsOpen,
  children,
}: ToolShellProps) {
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [supportOpen, setSupportOpen] = useState(false);
  const activeTool = tools.find((tool) => tool.id === activeToolId) ?? tools[0];
  const activeName = toolTitle(activeTool, settingsOpen);
  const lastUser = explicitLastUser ?? snapshot?.auth.last_user ?? "";

  function openSupport() {
    onOpenSupport?.();
    setSupportOpen(true);
  }

  return (
    <main className="app-shell">
      <section className="window-surface">
        <header className="shell-header" data-tauri-drag-region onDoubleClick={() => runWindowAction("maximize")}>
          <div className="window-controls" aria-label="窗口控制" onDoubleClick={(event) => event.stopPropagation()}>
            <button aria-label="关闭窗口" className="window-control close" onClick={() => runWindowAction("close")} title="关闭" type="button" />
            <button aria-label="最小化窗口" className="window-control minimize" onClick={() => runWindowAction("minimize")} title="最小化" type="button" />
            <button aria-label="最大化或还原窗口" className="window-control maximize" onClick={() => runWindowAction("maximize")} title="最大化/还原" type="button" />
          </div>
          <div className="title-stack" data-tauri-drag-region>
            <h1>{activeName}</h1>
          </div>
          <div className="header-actions" onDoubleClick={(event) => event.stopPropagation()}>
            <button className="settings-button avatar-button" onClick={() => setUserMenuOpen((value) => !value)} type="button">
              {lastUser ? lastUser.slice(0, 1).toUpperCase() : "?"}
            </button>
            <button className="settings-button" onClick={openSupport} type="button">
              赞赏
            </button>
            <button className={settingsOpen ? "settings-button active" : "settings-button"} onClick={onOpenSettings} type="button">
              设置
            </button>
          </div>
        </header>

        <div className="shell-body">
          <aside className="tool-list" aria-label="工具列表">
            <div className="tool-stack">
              {tools.map((tool, index) => {
                const active = !settingsOpen && tool.id === activeToolId;
                const disabled = tool.enabled === false;
                const category = categoryLabels[tool.category] ?? tool.category;
                const previousCategory = index > 0 ? categoryLabels[tools[index - 1].category] ?? tools[index - 1].category : "";
                const label = tool.sidebar_label ?? tool.title;
                const detail = label === tool.title ? toolStatusText(tool) : `${tool.title} · ${toolStatusText(tool)}`;
                const dotState = disabled
                  ? "tool-dot"
                  : toolActivity[tool.id] === "running"
                    ? "tool-dot running"
                    : toolActivity[tool.id] === "success"
                      ? "tool-dot success"
                      : toolActivity[tool.id] === "error"
                        ? "tool-dot error"
                        : tool.supported_in_tauri
                          ? "tool-dot ready"
                          : "tool-dot";
                return (
                  <Fragment key={tool.id}>
                    {category !== previousCategory ? <div className="panel-title">{category}</div> : null}
                    <button
                      aria-current={active ? "page" : undefined}
                      className={["tool-item", active ? "active" : "", disabled ? "disabled-by-settings" : ""]
                        .filter(Boolean)
                        .join(" ")}
                      disabled={active || disabled}
                      onClick={() => onSelectTool(tool.id)}
                      title={detail}
                      type="button"
                    >
                      <span className="tool-item-main">
                        <span>{label}</span>
                      </span>
                      <span className={dotState} />
                    </button>
                  </Fragment>
                );
              })}
            </div>
          </aside>

          <section className="tool-panel" aria-label="当前工具表单">
            <ToolErrorBoundary>
              {children}
            </ToolErrorBoundary>
          </section>
        </div>
        <UserMenu lastUser={lastUser} open={userMenuOpen} onClose={() => setUserMenuOpen(false)} onLogout={onLogout} />
        <SupportPopup open={supportOpen} supportImage={supportImage} onClose={() => setSupportOpen(false)} />
      </section>
    </main>
  );
}

export default ToolShell;
