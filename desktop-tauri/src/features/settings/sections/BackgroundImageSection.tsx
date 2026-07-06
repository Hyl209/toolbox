import { SettingFileField, SettingToggleRow } from "./primitives";

const IMAGE_FILTERS = [
  {
    name: "图片文件",
    extensions: ["png", "jpg", "jpeg", "webp", "bmp"],
  },
];

type BackgroundImageSectionProps = {
  saving: boolean;
  backgroundEnabled: boolean;
  backgroundImage: string;
  onBackgroundEnabledChange: (checked: boolean) => void;
  onBackgroundImageChange: (value: string) => void;
};

export default function BackgroundImageSection({
  saving,
  backgroundEnabled,
  backgroundImage,
  onBackgroundEnabledChange,
  onBackgroundImageChange,
}: BackgroundImageSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>背景图片</span>
      <div className="settings-group-stack">
        <SettingToggleRow
          checked={backgroundEnabled}
          description="启用后会把本地图片叠加到窗口背景层；路径为空时仍使用默认渐变。"
          disabled={saving}
          label="启用背景图"
          onChange={onBackgroundEnabledChange}
        />
        <SettingFileField
          buttonLabel="选择图片"
          clearLabel="清除"
          description="支持 png、jpg、jpeg、webp、bmp；为避免扩大本地文件读取范围，请使用应用数据目录 hyl-toolbox/backgrounds 下的图片。"
          dialogTitle="选择背景图片"
          disabled={saving}
          filters={IMAGE_FILTERS}
          label="背景图片路径"
          onChange={onBackgroundImageChange}
          onClear={() => onBackgroundImageChange("")}
          placeholder="%APPDATA%\\hyl-toolbox\\backgrounds\\background.webp"
          value={backgroundImage}
        />
      </div>
    </section>
  );
}
