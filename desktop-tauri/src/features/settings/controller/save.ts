import { saveSettingsPatch, type SettingsSnapshot, type ToolItem } from "../../../api/tauri";
import { buildSettingsPatch, type SettingsDraftState } from "..";

type SaveSettingsArgs = {
  snapshot: SettingsSnapshot;
  drafts: SettingsDraftState;
  toolsById: ReadonlyMap<string, ToolItem>;
  onSaved: (snapshot: SettingsSnapshot) => void;
};

export async function saveSettingsSnapshot({
  snapshot,
  drafts,
  toolsById,
  onSaved,
}: SaveSettingsArgs): Promise<string> {
  const next = await saveSettingsPatch(
    buildSettingsPatch(
      {
        snapshot,
        drafts,
        toolsById,
      },
      `settings-${Date.now()}`,
    ),
  );
  onSaved(next);
  return "已保存";
}
