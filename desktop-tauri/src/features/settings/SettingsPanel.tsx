import { useEffect, useState } from "react";
import type { SettingsSnapshot, ToolItem } from "../../api/tauri";
import { uiText } from "../../uiText";
import { DEFAULT_THEME_COLORS, pluginConfigKey, type ThemeColors, type ThemeName } from ".";
import { useSettingsPanelController } from "./useSettingsPanelController";
import AccountPreferencesSection from "./sections/AccountPreferencesSection";
import DownloaderSettingsSection from "./sections/DownloaderSettingsSection";
import EnvironmentDependenciesSection from "./sections/EnvironmentDependenciesSection";
import SettingsSummarySection from "./sections/SettingsSummarySection";
import ThemeModeSection from "./sections/ThemeModeSection";
import ThemePaletteSection from "./sections/ThemePaletteSection";
import ToolBehaviorSection from "./sections/ToolBehaviorSection";
import ToolOutputDirsSection from "./sections/ToolOutputDirsSection";
import { BuiltinToolsSection, PluginStatusSection, SidebarOrderSection } from "./sections/VisibilitySections";
import WordFormatterSection from "./sections/WordFormatterSection";

type SettingsPanelProps = {
  snapshot: SettingsSnapshot | null;
  fallbackTools: readonly ToolItem[];
  loading: boolean;
  error: string;
  onSaved: (snapshot: SettingsSnapshot) => void;
  onPreviewThemeChange: (theme: ThemeName, colors: ThemeColors) => void;
};

const SETTINGS_SECTIONS = [
  { id: "general", label: "常规", title: "常规", description: "账号与配置状态。" },
  { id: "appearance", label: "外观", title: "外观", description: "主题和配色。" },
  { id: "paths", label: "目录", title: "目录", description: "默认输入输出位置。" },
  { id: "downloaders", label: "下载", title: "下载", description: "下载器默认行为。" },
  { id: "dependencies", label: "环境", title: "环境依赖", description: "集中查看外部运行时与后端依赖状态。" },
  { id: "wordformatter", label: uiText.settings.wordSection, title: uiText.settings.wordSectionTitle, description: "排版默认参数。" },
  { id: "tools", label: "工具", title: "工具", description: "工具与插件开关。" },
  { id: "sidebar", label: "侧栏", title: "侧栏", description: "工具显示顺序。" },
] as const;

type SettingsSectionId = (typeof SETTINGS_SECTIONS)[number]["id"];

export default function SettingsPanel({
  snapshot,
  fallbackTools,
  loading,
  error,
  onSaved,
  onPreviewThemeChange,
}: SettingsPanelProps) {
  const [activeSection, setActiveSection] = useState<SettingsSectionId>("general");
  const {
    drafts,
    saving,
    notice,
    builtinTools,
    pluginTools,
    orderedTools,
    enabledTools,
    modeText,
    setToolEnabled,
    setPluginEnabled,
    setRememberPassword,
    setAutoLogin,
    moveSidebarItem,
    updateTheme,
    updateCustomThemeEnabled,
    updateThemeColor,
    updateToolOutputDir,
    updateToolBehavior,
    updateFilesorterCategory,
    updateDownloader,
    updateWordFormatterOutputDir,
    updateWordFormatterPage,
    updateWordFormatterStyle,
    saveSettings,
    sidebarStatus,
    toolDisplayName,
    toolMetadata,
  } = useSettingsPanelController({ snapshot, fallbackTools, onSaved });

  const activeMeta = SETTINGS_SECTIONS.find((section) => section.id === activeSection) ?? SETTINGS_SECTIONS[0];

  useEffect(() => {
    const colors = drafts.customThemeEnabled ? drafts.themeColors[drafts.theme] : DEFAULT_THEME_COLORS[drafts.theme];
    onPreviewThemeChange(drafts.theme, colors);
  }, [drafts.customThemeEnabled, drafts.theme, drafts.themeColors, onPreviewThemeChange]);

  return (
    <div className="settings-panel settings-shell">
      <aside className="settings-nav">
        <div className="settings-nav-overview">
          <strong>设置</strong>
          <span>{modeText}</span>
        </div>
        <div className="settings-nav-list" role="tablist" aria-label="设置分组">
          {SETTINGS_SECTIONS.map((section) => (
            <button
              aria-selected={activeSection === section.id}
              className={`settings-nav-button ${activeSection === section.id ? "active" : ""}`}
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              role="tab"
              type="button"
            >
              <span>{section.label}</span>
            </button>
          ))}
        </div>
      </aside>

      <div className="settings-content">
        <section className="settings-card settings-section-hero">
          <span>{activeMeta.label}</span>
          <strong>{activeMeta.title}</strong>
          <p>{activeMeta.description}</p>
        </section>

        {error ? <div className="error-box">{error}</div> : null}
        {notice ? <div className="info-box">{notice}</div> : null}

        {activeSection === "general" ? (
          <div className="settings-group-stack">
            <SettingsSummarySection
              loading={loading}
              modeText={modeText}
              settingsPath={snapshot?.settings_path}
              enabledTools={enabledTools}
              disabledToolsCount={drafts.disabledTools.size}
              disabledPluginCount={drafts.disabledPlugins.size}
              sidebarOrderCount={snapshot?.sidebar_order.length ?? 0}
              error=""
              notice=""
            />
            <AccountPreferencesSection
              lastUser={snapshot?.auth.last_user}
              rememberPassword={drafts.rememberPassword}
              autoLogin={drafts.autoLogin}
              onRememberPasswordChange={setRememberPassword}
              onAutoLoginChange={setAutoLogin}
            />
          </div>
        ) : null}

        {activeSection === "appearance" ? (
          <div className="settings-group-stack">
            <ThemeModeSection
              theme={drafts.theme}
              customThemeEnabled={drafts.customThemeEnabled}
              onThemeChange={updateTheme}
              onCustomThemeEnabledChange={updateCustomThemeEnabled}
            />
            <ThemePaletteSection
              theme={drafts.theme}
              themeColors={drafts.themeColors}
              onChange={updateThemeColor}
            />
          </div>
        ) : null}

        {activeSection === "paths" ? (
          <ToolOutputDirsSection saving={saving} toolOutputDirs={drafts.toolOutputDirs} onChange={updateToolOutputDir} />
        ) : null}

        {activeSection === "downloaders" ? (
          <DownloaderSettingsSection saving={saving} downloader={drafts.downloader} onChange={updateDownloader} />
        ) : null}

        {activeSection === "dependencies" ? <EnvironmentDependenciesSection /> : null}

        {activeSection === "wordformatter" ? (
          <WordFormatterSection
            saving={saving}
            draft={drafts.wordFormatter}
            onOutputDirChange={updateWordFormatterOutputDir}
            onPageChange={updateWordFormatterPage}
            onStyleChange={updateWordFormatterStyle}
          />
        ) : null}

        {activeSection === "tools" ? (
          <div className="settings-group-stack">
            <ToolBehaviorSection
              saving={saving}
              toolBehavior={drafts.toolBehavior}
              onBehaviorChange={updateToolBehavior}
              onFilesorterCategoryChange={updateFilesorterCategory}
            />
            <BuiltinToolsSection
              builtinTools={builtinTools}
              disabledTools={drafts.disabledTools}
              onToggle={setToolEnabled}
              toolDisplayName={toolDisplayName}
              toolMetadata={toolMetadata}
            />
            <PluginStatusSection
              pluginTools={pluginTools}
              disabledPlugins={drafts.disabledPlugins}
              onToggle={setPluginEnabled}
              toolDisplayName={toolDisplayName}
              toolMetadata={toolMetadata}
              pluginConfigKey={pluginConfigKey}
            />
          </div>
        ) : null}

        {activeSection === "sidebar" ? (
          <SidebarOrderSection
            orderedTools={orderedTools}
            saving={saving}
            disabledTools={drafts.disabledTools}
            disabledPlugins={drafts.disabledPlugins}
            onMove={moveSidebarItem}
            toolMetadata={toolMetadata}
            sidebarStatus={sidebarStatus}
          />
        ) : null}

        <div className="settings-save-row settings-save-sticky">
          <span className="action-hint">{saving ? "正在写回设置…" : "改动只在点击保存后落盘。"}</span>
          <button className="primary-button" disabled={!snapshot || saving} onClick={saveSettings} type="button">
            {saving ? "保存中" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
