import { getCurrentWindow } from "@tauri-apps/api/window";
import { Fragment, type ReactNode } from "react";
import type { ToolItem } from "../api/tauri";

type ToolShellProps = {
  title: string;
  tools: readonly ToolItem[];
  activeToolId: string;
  onSelectTool: (toolId: string) => void;
  onOpenSettings: () => void;
  settingsOpen: boolean;
  children: ReactNode;
};

const categoryLabels: Record<string, string> = {
  audio: "\u97f3\u9891",
  document: "\u6587\u6863",
  download: "\u4e0b\u8f7d",
  file: "\u6587\u4ef6",
  image: "\u56fe\u7247",
  plugin: "\u63d2\u4ef6",
  text: "\u6587\u672c",
};

const statusLabels: Record<ToolItem["status"], string> = {
  planned: "\u8ba1\u5212\u4e2d",
  pending: "\u6682\u672a\u63a5\u5165",
  ready: "\u5df2\u63a5\u5165\u5165\u53e3",
};

const capabilityNotes: Record<string, string> = {
  tgdownloader: "\u90e8\u5206\u53ef\u7528 \u00b7 \u4e0b\u8f7d/\u767b\u5f55",
  webvideodownloader: "\u90e8\u5206\u53ef\u7528 \u00b7 \u4e0b\u8f7d/\u9884\u68c0",
};

const windowActions = {
  close: () => getCurrentWindow().close(),
  maximize: () => getCurrentWindow().toggleMaximize(),
  minimize: () => getCurrentWindow().minimize(),
};

function runWindowAction(action: keyof typeof windowActions) {
  if (!("__TAURI_INTERNALS__" in window)) {
    return;
  }
  void windowActions[action]();
}

function toolStatusText(tool: ToolItem): string {
  if (tool.enabled === false) {
    return "\u5df2\u7981\u7528";
  }
  const statusText = capabilityNotes[tool.id] ?? statusLabels[tool.status];
  if (tool.source === "plugin") {
    return `${statusText} \u00b7 \u63d2\u4ef6`;
  }
  return statusText;
}

function ToolShell({
  title,
  tools,
  activeToolId,
  onSelectTool,
  onOpenSettings,
  settingsOpen,
  children,
}: ToolShellProps) {
  const activeTool = tools.find((tool) => tool.id === activeToolId) ?? tools[0];
  const readyCount = tools.filter((tool) => tool.status === "ready" && tool.enabled !== false).length;
  const enabledCount = tools.filter((tool) => tool.enabled !== false).length;
  const activeCategory = settingsOpen ? "\u8bbe\u7f6e" : categoryLabels[activeTool?.category ?? ""] ?? activeTool?.category ?? "\u5de5\u5177";
  const activeName = settingsOpen ? "\u8bbe\u7f6e" : activeTool?.sidebar_label ?? activeTool?.title ?? "\u5de5\u5177";

  return (
    <main className="app-shell">
      <section className="window-surface">
        <header className="shell-header" data-tauri-drag-region onDoubleClick={() => runWindowAction("maximize")}>
          <div className="window-controls" aria-label="\u7a97\u53e3\u63a7\u5236" onDoubleClick={(event) => event.stopPropagation()}>
            <button aria-label="\u5173\u95ed\u7a97\u53e3" className="window-control close" onClick={() => runWindowAction("close")} title="\u5173\u95ed" type="button" />
            <button aria-label="\u6700\u5c0f\u5316\u7a97\u53e3" className="window-control minimize" onClick={() => runWindowAction("minimize")} title="\u6700\u5c0f\u5316" type="button" />
            <button aria-label="\u6700\u5927\u5316\u6216\u8fd8\u539f\u7a97\u53e3" className="window-control maximize" onClick={() => runWindowAction("maximize")} title="\u6700\u5927\u5316/\u8fd8\u539f" type="button" />
          </div>
          <div className="title-stack" data-tauri-drag-region>
            <p className="eyebrow">Desktop utility studio</p>
            <h1>{title}</h1>
          </div>
          <div className="header-actions" onDoubleClick={(event) => event.stopPropagation()}>
            <div className="status-pill" aria-label={`${readyCount} \u4e2a\u5df2\u63a5\u5165\u5165\u53e3`}>
              <span className="pulse-dot" />
              {readyCount}/{enabledCount} {"\u5df2\u63a5\u5165\u5165\u53e3"}
            </div>
            <button className={settingsOpen ? "settings-button active" : "settings-button"} onClick={onOpenSettings} type="button">
              {"\u8bbe\u7f6e"}
            </button>
          </div>
        </header>

        <div className="shell-body">
          <aside className="tool-list" aria-label="\u5de5\u5177\u5217\u8868">
            <div className="sidebar-intro">
              <span>Workspace</span>
              <strong>{activeName}</strong>
              <small>{activeCategory}</small>
            </div>

            <div className="tool-stack">
              {tools.map((tool, index) => {
                const active = !settingsOpen && tool.id === activeToolId;
                const disabled = tool.enabled === false;
                const category = categoryLabels[tool.category] ?? tool.category;
                const previousCategory = index > 0 ? categoryLabels[tools[index - 1].category] ?? tools[index - 1].category : "";
                const label = tool.sidebar_label ?? tool.title;
                const detail = label === tool.title ? toolStatusText(tool) : `${tool.title} \u00b7 ${toolStatusText(tool)}`;
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
                      type="button"
                    >
                      <span className="tool-item-main">
                        <span>{label}</span>
                        <small>{detail}</small>
                      </span>
                      <span className={tool.supported_in_tauri && !disabled ? "tool-dot ready" : "tool-dot"} />
                    </button>
                  </Fragment>
                );
              })}
            </div>
          </aside>

          <section className="tool-panel" aria-label="\u5f53\u524d\u5de5\u5177\u8868\u5355">
            {children}
          </section>
        </div>
      </section>
    </main>
  );
}

export default ToolShell;
