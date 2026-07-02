import { THEME_NAMES, type ThemeName } from "..";
import { SettingToggleRow } from "./primitives";

type ThemeModeSectionProps = {
  theme: ThemeName;
  customThemeEnabled: boolean;
  onThemeChange: (theme: ThemeName) => void;
  onCustomThemeEnabledChange: (checked: boolean) => void;
};

export default function ThemeModeSection({
  theme,
  customThemeEnabled,
  onThemeChange,
  onCustomThemeEnabledChange,
}: ThemeModeSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>主题模式</span>
      <div className="settings-control-row settings-mode-row">
        <div className="mode-switch">
          {THEME_NAMES.map((themeName) => (
            <button className={theme === themeName ? "active" : ""} key={themeName} onClick={() => onThemeChange(themeName)} type="button">
              {themeName === "dark" ? "暗色" : "亮色"}
            </button>
          ))}
        </div>
        <div className="settings-mode-toggle">
          <SettingToggleRow
            checked={customThemeEnabled}
            description="暗色和亮色都会各自保存一套草稿，开关只控制是否启用自定义主题。"
            label="启用自定义主题"
            onChange={onCustomThemeEnabledChange}
          />
        </div>
      </div>
    </section>
  );
}
