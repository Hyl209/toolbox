import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";
import { loadSettingsSnapshot, TOOL_ACTIVITY_EVENT, type SettingsSnapshot, type ToolActivityState, type ToolItem } from "./api/tauri";
import ToolShell from "./components/ToolShell";
import SettingsPanel from "./features/settings/SettingsPanel";
import { firstSelectableTool, themeStyle, themeStyleFromColors, type ThemeColors, type ThemeName } from "./features/settings";
import { fallbackTools, renderToolPanel, sidebarToolsFromSnapshot } from "./features/tools";
import "./styles.css";

function pickFirstTool(tools: readonly ToolItem[]): ToolItem {
  return firstSelectableTool(tools) ?? tools[0] ?? fallbackTools[0];
}

function App() {
  const [snapshot, setSnapshot] = useState<SettingsSnapshot | null>(null);
  const [settingsError, setSettingsError] = useState("");
  const [activeToolId, setActiveToolId] = useState(fallbackTools[0].id);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [previewTheme, setPreviewTheme] = useState<{ mode: ThemeName; style: CSSProperties } | null>(null);
  const [toolActivity, setToolActivity] = useState<Record<string, ToolActivityState>>({});

  useEffect(() => {
    let cancelled = false;
    loadSettingsSnapshot()
      .then((data) => {
        if (cancelled) {
          return;
        }
        const sidebarTools = sidebarToolsFromSnapshot(data.tools);
        setSnapshot(data);
        setSettingsError("");
        setActiveToolId(pickFirstTool(sidebarTools).id);
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

  function selectTool(toolId: string) {
    setSettingsOpen(false);
    setPreviewTheme(null);
    setActiveToolId(toolId);
    setToolActivity((current) => ({ ...current, [toolId]: "ready" }));
  }

  function toggleSettings() {
    setSettingsOpen((value) => {
      const next = !value;
      if (!next) {
        setPreviewTheme(null);
      }
      return next;
    });
  }

  const handlePreviewThemeChange = useCallback((mode: ThemeName, colors: ThemeColors) => {
    setPreviewTheme({ mode, style: themeStyleFromColors(colors) });
  }, []);

  function handleSettingsSaved(nextSnapshot: SettingsSnapshot) {
    const nextSidebarTools = sidebarToolsFromSnapshot(nextSnapshot.tools);
    setSnapshot(nextSnapshot);
    setPreviewTheme(null);
    if (!nextSidebarTools.some((tool) => tool.id === activeToolId)) {
      setActiveToolId(pickFirstTool(nextSidebarTools).id);
    }
  }

  return (
    <div className="theme-root" style={previewTheme?.style ?? themeStyle(snapshot)} data-theme-mode={previewTheme?.mode ?? snapshot?.ui.theme ?? "light"}>
      <ToolShell
        title="Hyl Toolbox"
        tools={sidebarTools}
        toolActivity={toolActivity}
        activeToolId={activeTool.id}
        onSelectTool={selectTool}
        onOpenSettings={toggleSettings}
        settingsOpen={settingsOpen}
      >
        {settingsOpen ? (
          <SettingsPanel
            snapshot={snapshot}
            fallbackTools={allTools}
            loading={!snapshot && !settingsError}
            error={settingsError}
            onSaved={handleSettingsSaved}
            onPreviewThemeChange={handlePreviewThemeChange}
          />
        ) : (
          renderToolPanel(activeTool, snapshot)
        )}
      </ToolShell>
    </div>
  );
}

export default App;
