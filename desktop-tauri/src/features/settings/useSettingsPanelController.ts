import { useEffect, useMemo, useRef, useState } from "react";
import type { SettingsSnapshot, ToolItem } from "../../api/tauri";
import {
  createSettingsDraftState,
  toolDisplayName,
  toolMetadata,
  type DownloaderSettingsId,
  type ThemeName,
  type ThemeZone,
  type ToolBehaviorSettingsId,
  type WordFormatterPageKey,
  type WordFormatterStyleField,
  type WordFormatterStyleKey,
} from ".";
import {
  moveSidebarItem as moveSidebarItemDraft,
  toggleBuiltinTool,
  togglePlugin,
  updateAutoLogin as updateAutoLoginDraft,
  updateBackgroundEnabled as updateBackgroundEnabledDraft,
  updateBackgroundImage as updateBackgroundImageDraft,
  updateBackgroundOpacity as updateBackgroundOpacityDraft,
  updateCustomThemeEnabled as updateCustomThemeEnabledDraft,
  updateDownloader as updateDownloaderDraft,
  updateFilesorterCategory as updateFilesorterCategoryDraft,
  updateRememberPassword as updateRememberPasswordDraft,
  updateTheme as updateThemeDraft,
  updateThemeColor as updateThemeColorDraft,
  updateToolBehavior as updateToolBehaviorDraft,
  updateToolOutputDir as updateToolOutputDirDraft,
  updateWordFormatterOutputDir as updateWordFormatterOutputDirDraft,
  updateWordFormatterPage as updateWordFormatterPageDraft,
  updateWordFormatterStyle as updateWordFormatterStyleDraft,
} from "./controller/actions";
import { deriveSettingsCollections } from "./controller/derived";
import { saveSettingsSnapshot } from "./controller/save";
import { sidebarStatus } from "./controller/viewState";

type UseSettingsPanelControllerArgs = {
  snapshot: SettingsSnapshot | null;
  fallbackTools: readonly ToolItem[];
  onSaved: (snapshot: SettingsSnapshot) => void;
};

export function useSettingsPanelController({ snapshot, fallbackTools, onSaved }: UseSettingsPanelControllerArgs) {
  const [drafts, setDrafts] = useState(() => createSettingsDraftState(snapshot, fallbackTools));
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    setDrafts(createSettingsDraftState(snapshot, fallbackTools));
    setNotice("");
  }, [snapshot, fallbackTools]);

  const {
    builtinTools,
    pluginTools,
    toolsById,
    orderedTools,
    enabledTools,
    modeText,
  } = useMemo(
    () =>
      deriveSettingsCollections({
        snapshot,
        fallbackTools,
        drafts,
      }),
    [snapshot, fallbackTools, drafts],
  );
  const builtinToolsRef = useRef(builtinTools);
  builtinToolsRef.current = builtinTools;
  const pluginToolsRef = useRef(pluginTools);
  pluginToolsRef.current = pluginTools;

  function applyDraftMutation(mutator: (current: typeof drafts) => typeof drafts, nextNotice = "") {
    setDrafts((current) => mutator(current));
    setNotice(nextNotice);
  }

  function setToolEnabled(toolId: string, enabled: boolean) {
    setDrafts((current) => {
      const result = toggleBuiltinTool(current, builtinToolsRef.current, toolId, enabled);
      setNotice(result.notice ?? "");
      return result.next;
    });
  }

  function setPluginEnabled(tool: ToolItem, enabled: boolean) {
    setDrafts((current) => {
      const result = togglePlugin(current, pluginToolsRef.current, tool, enabled);
      setNotice(result.notice ?? "");
      return result.next;
    });
  }

  function setRememberPassword(checked: boolean) {
    applyDraftMutation((current) => updateRememberPasswordDraft(current, checked));
  }

  function setAutoLogin(checked: boolean) {
    applyDraftMutation((current) => updateAutoLoginDraft(current, checked));
  }

  function moveSidebarItem(toolId: string, direction: -1 | 1) {
    applyDraftMutation((current) => moveSidebarItemDraft(current, toolId, direction));
  }

  function updateTheme(value: ThemeName) {
    applyDraftMutation((current) => updateThemeDraft(current, value));
  }

  function updateCustomThemeEnabled(checked: boolean) {
    applyDraftMutation((current) => updateCustomThemeEnabledDraft(current, checked));
  }

  function updateBackgroundEnabled(checked: boolean) {
    applyDraftMutation((current) => updateBackgroundEnabledDraft(current, checked));
  }

  function updateBackgroundImage(value: string) {
    applyDraftMutation((current) => updateBackgroundImageDraft(current, value));
  }

  function updateBackgroundOpacity(value: number) {
    applyDraftMutation((current) => updateBackgroundOpacityDraft(current, value));
  }

  function updateThemeColor(zone: ThemeZone, value: string) {
    applyDraftMutation((current) => updateThemeColorDraft(current, zone, value));
  }

  function updateToolOutputDir(toolId: keyof typeof drafts.toolOutputDirs, value: string) {
    applyDraftMutation((current) => updateToolOutputDirDraft(current, toolId, value));
  }

  function updateToolBehavior<T extends ToolBehaviorSettingsId, K extends keyof (typeof drafts.toolBehavior)[T]>(
    toolId: T,
    key: K,
    value: (typeof drafts.toolBehavior)[T][K],
  ) {
    applyDraftMutation((current) => updateToolBehaviorDraft(current, toolId, key, value));
  }

  function updateFilesorterCategory(category: string, enabled: boolean) {
    applyDraftMutation((current) => updateFilesorterCategoryDraft(current, category, enabled));
  }

  function updateDownloader<T extends DownloaderSettingsId, K extends keyof (typeof drafts.downloader)[T]>(
    toolId: T,
    key: K,
    value: (typeof drafts.downloader)[T][K],
  ) {
    applyDraftMutation((current) => updateDownloaderDraft(current, toolId, key, value));
  }

  function updateWordFormatterOutputDir(value: string) {
    applyDraftMutation((current) => updateWordFormatterOutputDirDraft(current, value));
  }

  function updateWordFormatterPage(key: WordFormatterPageKey, value: string) {
    applyDraftMutation((current) => updateWordFormatterPageDraft(current, key, value));
  }

  function updateWordFormatterStyle(styleKey: WordFormatterStyleKey, field: WordFormatterStyleField, value: string | boolean) {
    applyDraftMutation((current) => updateWordFormatterStyleDraft(current, styleKey, field, value));
  }

  async function saveSettings() {
    if (!snapshot || saving) {
      return;
    }
    setSaving(true);
    setNotice("");
    try {
      const message = await saveSettingsSnapshot({
        snapshot,
        drafts,
        toolsById,
        onSaved,
      });
      setNotice(message);
    } catch (caught: unknown) {
      setNotice(caught instanceof Error ? caught.message : String(caught));
    } finally {
      setSaving(false);
    }
  }

  return {
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
    updateBackgroundEnabled,
    updateBackgroundImage,
    updateBackgroundOpacity,
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
  };
}
