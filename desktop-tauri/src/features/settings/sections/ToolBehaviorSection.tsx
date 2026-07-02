import { FILESORTER_CATEGORIES, type ToolBehaviorDraft } from "..";
import { SettingDirectoryField, SettingSelectField, SettingTextField, SettingToggleRow } from "./primitives";

type ToolBehaviorSectionProps = {
  saving: boolean;
  toolBehavior: ToolBehaviorDraft;
  onBehaviorChange: <T extends keyof ToolBehaviorDraft, K extends keyof ToolBehaviorDraft[T]>(
    toolId: T,
    key: K,
    value: ToolBehaviorDraft[T][K],
  ) => void;
  onFilesorterCategoryChange: (category: string, enabled: boolean) => void;
};

export default function ToolBehaviorSection({
  saving,
  toolBehavior,
  onBehaviorChange,
  onFilesorterCategoryChange,
}: ToolBehaviorSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>工具行为偏好</span>
      <p>只保留真正会影响默认行为的参数，把批量命名、文件分类、重复文件和直链下载分开管理。</p>

      <div className="settings-group-stack">
        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>批量命名</strong>
            <p>设置默认输入目录、命名前缀和排序策略。</p>
          </header>
          <div className="settings-two-column-grid">
            <SettingDirectoryField
              disabled={saving}
              dialogTitle="选择批量命名默认输入目录"
              label="默认输入目录"
              meta="batchrename/input_dir"
              onChange={(value) => onBehaviorChange("batchrename", "input_dir", value)}
              value={toolBehavior.batchrename.input_dir}
            />
            <SettingTextField
              disabled={saving}
              label="命名前缀"
              meta="batchrename/prefix"
              onChange={(value) => onBehaviorChange("batchrename", "prefix", value)}
              value={toolBehavior.batchrename.prefix}
            />
            <SettingSelectField
              disabled={saving}
              label="分组方式"
              meta="batchrename/group_mode"
              onChange={(value) => onBehaviorChange("batchrename", "group_mode", value)}
              options={[
                { label: "按后缀", value: "按后缀" },
                { label: "按类型", value: "按类型" },
                { label: "全文件", value: "全文件" },
              ]}
              value={toolBehavior.batchrename.group_mode}
            />
            <SettingSelectField
              disabled={saving}
              label="排序字段"
              meta="batchrename/sort_mode"
              onChange={(value) => onBehaviorChange("batchrename", "sort_mode", value)}
              options={[
                { label: "按命名", value: "按命名" },
                { label: "修改日期", value: "修改日期" },
                { label: "文件大小", value: "文件大小" },
              ]}
              value={toolBehavior.batchrename.sort_mode}
            />
            <SettingSelectField
              disabled={saving}
              label="排序方向"
              meta="batchrename/sort_order"
              onChange={(value) => onBehaviorChange("batchrename", "sort_order", value)}
              options={[
                { label: "从小到大", value: "从小到大" },
                { label: "从大到小", value: "从大到小" },
              ]}
              value={toolBehavior.batchrename.sort_order}
            />
          </div>
        </section>

        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>文件分类</strong>
            <p>控制默认输入目录、分类模式和启用的大类。</p>
          </header>
          <div className="settings-group-stack">
            <div className="settings-two-column-grid">
              <SettingDirectoryField
                disabled={saving}
                dialogTitle="选择文件分类默认输入目录"
                label="默认输入目录"
                meta="filesorter/input_dir"
                onChange={(value) => onBehaviorChange("filesorter", "input_dir", value)}
                value={toolBehavior.filesorter.input_dir}
              />
              <SettingSelectField
                disabled={saving}
                label="分类模式"
                meta="filesorter/mode"
                onChange={(value) => onBehaviorChange("filesorter", "mode", value)}
                options={[
                  { label: "按大类分类", value: "按大类分类" },
                  { label: "按分辨率分类", value: "按分辨率分类" },
                ]}
                value={toolBehavior.filesorter.mode}
              />
            </div>
            <div className="settings-toggle-grid">
              {FILESORTER_CATEGORIES.map((category) => (
                <SettingToggleRow
                  checked={toolBehavior.filesorter.categories[category]}
                  description="决定该分类是否默认参与整理。"
                  disabled={saving}
                  key={category}
                  label={category}
                  meta={`filesorter/category_${category}`}
                  onChange={(checked) => onFilesorterCategoryChange(category, checked)}
                />
              ))}
            </div>
          </div>
        </section>

        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>重复文件</strong>
            <p>控制默认扫描目录以及是否递归处理子目录。</p>
          </header>
          <div className="settings-two-column-grid">
            <SettingDirectoryField
              disabled={saving}
              dialogTitle="选择重复文件默认输入目录"
              label="默认输入目录"
              meta="same/input_dir"
              onChange={(value) => onBehaviorChange("same", "input_dir", value)}
              value={toolBehavior.same.input_dir}
            />
            <SettingToggleRow
              checked={toolBehavior.same.recursive}
              description="启用后会一起扫描子目录。"
              disabled={saving}
              label="递归扫描"
              meta="same/recursive"
              onChange={(checked) => onBehaviorChange("same", "recursive", checked)}
            />
          </div>
        </section>

        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>直链下载</strong>
            <p>保留默认连接数、代理和 Referer 等兼容参数。</p>
          </header>
          <div className="settings-two-column-grid">
            <SettingTextField
              disabled={saving}
              label="连接数"
              meta="directdownloader/connections"
              onChange={(value) => onBehaviorChange("directdownloader", "connections", value)}
              value={toolBehavior.directdownloader.connections}
            />
            <SettingTextField
              disabled={saving}
              label="代理 URL"
              meta="directdownloader/proxy_url"
              onChange={(value) => onBehaviorChange("directdownloader", "proxy_url", value)}
              value={toolBehavior.directdownloader.proxy_url}
            />
            <SettingTextField
              disabled={saving}
              label="Referer"
              meta="directdownloader/referer"
              onChange={(value) => onBehaviorChange("directdownloader", "referer", value)}
              value={toolBehavior.directdownloader.referer}
            />
          </div>
          <div className="settings-toggle-grid">
            <SettingToggleRow
              checked={toolBehavior.directdownloader.overwrite}
              description="允许覆盖已存在文件。"
              disabled={saving}
              label="覆盖已存在文件"
              meta="directdownloader/overwrite"
              onChange={(checked) => onBehaviorChange("directdownloader", "overwrite", checked)}
            />
            <SettingToggleRow
              checked={toolBehavior.directdownloader.output_subdir_by_filename}
              description="按文件名拆分输出子目录。"
              disabled={saving}
              label="按文件名创建子目录"
              meta="directdownloader/output_subdir_by_filename"
              onChange={(checked) => onBehaviorChange("directdownloader", "output_subdir_by_filename", checked)}
            />
          </div>
        </section>
      </div>
    </section>
  );
}
