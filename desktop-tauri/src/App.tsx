import { convertFileSrc } from "@tauri-apps/api/core";
import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  loadSettingsSnapshot,
  loadSupportImage,
  logoutCurrentUser,
  TOOL_ACTIVITY_EVENT,
  type SettingsSnapshot,
  type ToolActivityState,
  type ToolItem,
} from "./api/tauri";
import ToolShell from "./components/ToolShell";
import SettingsPanel from "./features/settings/SettingsPanel";
import { firstSelectableTool, themeStyle, themeStyleFromColors, type ThemeColors, type ThemeName } from "./features/settings";
import { fallbackTools, renderKeepAliveToolPanels, sidebarToolsFromSnapshot } from "./features/tools";
import { uiText } from "./uiText";
import "./styles.css";

function pickFirstTool(tools: readonly ToolItem[]): ToolItem {
  return firstSelectableTool(tools) ?? tools[0] ?? fallbackTools[0];
}

function backgroundFileUrl(filePath: string): string {
  if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
    return convertFileSrc(filePath);
  }
  const normalized = filePath.replace(/\\/g, "/");
  return normalized.startsWith("/") ? `file://${normalized}` : `file:///${normalized}`;
}

function backgroundImageStyle(snapshot: SettingsSnapshot | null): CSSProperties {
  const imagePath = snapshot?.ui.background_enabled ? snapshot.ui.background_image.trim() : "";
  if (!imagePath) {
    return {};
  }
  const imageUrl = backgroundFileUrl(imagePath).replace(/"/g, '\\"');
  const opacity = Math.max(0, Math.min(100, snapshot?.ui.background_opacity ?? 100)) / 100;
  return {
    "--window-background-image": `url("${imageUrl}")`,
    "--window-background-opacity": String(opacity),
  } as CSSProperties;
}

function App() {
  const [snapshot, setSnapshot] = useState<SettingsSnapshot | null>(null);
  const [settingsError, setSettingsError] = useState("");
  const [activeToolId, setActiveToolId] = useState(fallbackTools[0].id);
  const [visitedToolIds, setVisitedToolIds] = useState<string[]>([fallbackTools[0].id]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [previewTheme, setPreviewTheme] = useState<{ mode: ThemeName; style: CSSProperties } | null>(null);
  const [toolActivity, setToolActivity] = useState<Record<string, ToolActivityState>>({});
  const [supportImage, setSupportImage] = useState("");

  useEffect(() => {
    let cancelled = false;
    loadSettingsSnapshot()
      .then((data) => {
        if (cancelled) {
          return;
        }
        const sidebarTools = sidebarToolsFromSnapshot(data.tools);
        const firstTool = pickFirstTool(sidebarTools);
        setSnapshot(data);
        setSettingsError("");
        setActiveToolId(firstTool.id);
        setVisitedToolIds([firstTool.id]);
      })
      .catch((caught: unknown) => {
        if (cancelled) {
          return;
        }
        setSettingsError(caught instanceof Error ? caught.message : String(caught));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    loadSupportImage().then((image) => {
      if (!cancelled) {
        setSupportImage(image);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    function handleToolActivity(event: Event) {
      const detail = (event as CustomEvent<{ toolId: string; state: ToolActivityState }>).detail;
      if (!detail?.toolId || !detail?.state) {
        return;
      }
      setToolActivity((current) => ({ ...current, [detail.toolId]: detail.state }));
    }

    window.addEventListener(TOOL_ACTIVITY_EVENT, handleToolActivity);
    return () => window.removeEventListener(TOOL_ACTIVITY_EVENT, handleToolActivity);
  }, []);

  const allTools = snapshot?.tools?.length ? snapshot.tools : fallbackTools;
  const sidebarTools = useMemo(() => sidebarToolsFromSnapshot(allTools), [allTools]);
  const activeTool = useMemo(
    () => sidebarTools.find((tool) => tool.id === activeToolId) ?? pickFirstTool(sidebarTools),
    [activeToolId, sidebarTools],
  );

  useEffect(() => {
    setVisitedToolIds((current) => (current.includes(activeTool.id) ? current : [...current, activeTool.id]));
  }, [activeTool.id]);

  function withTransition(update: () => void) {
    if ("startViewTransition" in document) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (document as any).startViewTransition(update);
    } else {
      update();
    }
  }

  function selectTool(toolId: string) {
    withTransition(() => {
      setSettingsOpen(false);
      setPreviewTheme(null);
      setActiveToolId(toolId);
      setVisitedToolIds((current) => (current.includes(toolId) ? current : [...current, toolId]));
      setToolActivity((current) => ({ ...current, [toolId]: "ready" }));
    });
  }

  function toggleSettings() {
    withTransition(() => {
      setSettingsOpen((value) => {
        const next = !value;
        if (!next) {
          setPreviewTheme(null);
        }
        return next;
      });
    });
  }

  const handlePreviewThemeChange = useCallback((mode: ThemeName, colors: ThemeColors) => {
    setPreviewTheme({ mode, style: themeStyleFromColors(colors) });
  }, []);

  function handleSettingsSaved(nextSnapshot: SettingsSnapshot) {
    const nextSidebarTools = sidebarToolsFromSnapshot(nextSnapshot.tools);
    const nextActiveTool = nextSidebarTools.some((tool) => tool.id === activeToolId)
      ? activeToolId
      : pickFirstTool(nextSidebarTools).id;
    setSnapshot(nextSnapshot);
    setPreviewTheme(null);
    setVisitedToolIds((current) => {
      const available = new Set(nextSidebarTools.map((tool) => tool.id));
      const kept = current.filter((toolId) => available.has(toolId));
      return kept.includes(nextActiveTool) ? kept : [...kept, nextActiveTool];
    });
    if (nextActiveTool !== activeToolId) {
      setActiveToolId(nextActiveTool);
    }
  }

  async function handleLogout() {
    await logoutCurrentUser();
    const nextSnapshot = await loadSettingsSnapshot();
    setSnapshot(nextSnapshot);
  }

  const rootStyle = useMemo(
    () => ({
      ...(previewTheme?.style ?? themeStyle(snapshot)),
      ...backgroundImageStyle(snapshot),
    }),
    [previewTheme?.style, snapshot],
  );
  const backgroundImageActive = Boolean(snapshot?.ui.background_enabled && snapshot.ui.background_image.trim());

  return (
    <div
      className="theme-root"
      style={rootStyle}
      data-theme-mode={previewTheme?.mode ?? snapshot?.ui.theme ?? "light"}
      data-background-image={backgroundImageActive ? "true" : "false"}
    >
      <ToolShell
        title={uiText.app.title}
        tools={sidebarTools}
        toolActivity={toolActivity}
        activeToolId={activeTool.id}
        lastUser={snapshot?.auth.last_user ?? ""}
        supportImage={supportImage}
        onLogout={handleLogout}
        onSelectTool={selectTool}
        onOpenSettings={toggleSettings}
        settingsOpen={settingsOpen}
      >
        <div className="tool-panel-viewport">
          <div className={settingsOpen ? "keep-alive-tool-stack hidden" : "keep-alive-tool-stack"} aria-hidden={settingsOpen}>
            {renderKeepAliveToolPanels(sidebarTools, activeTool.id, visitedToolIds, snapshot)}
          </div>
          {settingsOpen ? (
            <SettingsPanel
              snapshot={snapshot}
              fallbackTools={allTools}
              loading={!snapshot && !settingsError}
              error={settingsError}
              onSaved={handleSettingsSaved}
              onPreviewThemeChange={handlePreviewThemeChange}
            />
          ) : null}
        </div>
      </ToolShell>
    </div>
  );
}

export default App;
