import { TOOL_OUTPUT_DIRS, type ToolOutputDirDraft } from "..";
import { SettingOutputDirRow } from "./primitives";

type ToolOutputDirsSectionProps = {
  saving: boolean;
  toolOutputDirs: ToolOutputDirDraft;
  onChange: (toolId: (typeof TOOL_OUTPUT_DIRS)[number]["id"], value: string) => void;
};

export default function ToolOutputDirsSection({ saving, toolOutputDirs, onChange }: ToolOutputDirsSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>工具默认目录</span>
      <p>统一维护已迁移工具的输出目录；留空表示沿用运行时默认位置。</p>
      <div className="settings-two-column-grid">
        {TOOL_OUTPUT_DIRS.map((tool) => (
          <SettingOutputDirRow
            description="保存后会回写旧版 output_dir 配置。"
            disabled={saving}
            key={tool.id}
            label={tool.label}
            onChange={(value) => onChange(tool.id, value)}
            pathKey={`${tool.id}/output_dir`}
            value={toolOutputDirs[tool.id]}
          />
        ))}
      </div>
    </section>
  );
}
