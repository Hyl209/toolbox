import {
  type WordFormatterDraft,
  type WordFormatterPageKey,
  type WordFormatterStyleField,
  type WordFormatterStyleKey,
  WORD_FORMATTER_FIELD_LABELS,
  WORD_FORMATTER_PAGE_KEYS,
  WORD_FORMATTER_PAGE_LABELS,
  WORD_FORMATTER_PAGE_SETTING_KEYS,
  WORD_FORMATTER_STYLE_FIELDS,
  WORD_FORMATTER_STYLE_KEYS,
  WORD_FORMATTER_STYLE_SETTING_KEYS,
  WORD_FORMATTER_STYLE_TITLES,
} from "..";
import { SettingOutputDirRow, SettingTextField, SettingToggleRow } from "./primitives";

type WordFormatterSectionProps = {
  saving: boolean;
  draft: WordFormatterDraft;
  onOutputDirChange: (value: string) => void;
  onPageChange: (key: WordFormatterPageKey, value: string) => void;
  onStyleChange: (styleKey: WordFormatterStyleKey, field: WordFormatterStyleField, value: string | boolean) => void;
};

export default function WordFormatterSection({
  saving,
  draft,
  onOutputDirChange,
  onPageChange,
  onStyleChange,
}: WordFormatterSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>Word 排版</span>
      <p>把输出目录、页面参数和样式参数分开编辑，避免全部字段同屏堆叠。</p>

      <div className="settings-group-stack">
        <SettingOutputDirRow
          description="保存统一排版后的文档输出目录。"
          disabled={saving}
          label="默认输出目录"
          onChange={onOutputDirChange}
          pathKey="wordformatter/output_dir"
          value={draft.output_dir}
        />

        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>页面设置</strong>
            <p>统一控制页边距、页眉和页脚距离。</p>
          </header>
          <div className="settings-two-column-grid">
            {WORD_FORMATTER_PAGE_KEYS.map((key) => (
              <SettingTextField
                disabled={saving}
                key={key}
                label={WORD_FORMATTER_PAGE_LABELS[key]}
                meta={WORD_FORMATTER_PAGE_SETTING_KEYS[key]}
                onChange={(value) => onPageChange(key, value)}
                value={draft.page[key]}
              />
            ))}
          </div>
        </section>

        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>样式设置</strong>
            <p>每种文本样式单独折叠，展开后再编辑详细参数。</p>
          </header>
          <div className="settings-group-stack">
            {WORD_FORMATTER_STYLE_KEYS.map((styleKey) => (
              <details className="settings-detail-card" key={styleKey}>
                <summary>
                  <span>{WORD_FORMATTER_STYLE_TITLES[styleKey]}</span>
                  <small>{WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey].font}</small>
                </summary>
                <div className="settings-two-column-grid">
                  {WORD_FORMATTER_STYLE_FIELDS.map((field) =>
                    field === "bold" ? (
                      <SettingToggleRow
                        checked={Boolean(draft.styles[styleKey].bold)}
                        description="控制该样式是否默认加粗。"
                        disabled={saving}
                        key={`${styleKey}-${field}`}
                        label={WORD_FORMATTER_FIELD_LABELS.bold}
                        meta={WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey].bold}
                        onChange={(checked) => onStyleChange(styleKey, "bold", checked)}
                      />
                    ) : (
                      <SettingTextField
                        disabled={saving}
                        key={`${styleKey}-${field}`}
                        label={WORD_FORMATTER_FIELD_LABELS[field]}
                        meta={WORD_FORMATTER_STYLE_SETTING_KEYS[styleKey][field]}
                        onChange={(value) => onStyleChange(styleKey, field, value)}
                        value={String(draft.styles[styleKey][field])}
                      />
                    ),
                  )}
                </div>
              </details>
            ))}
          </div>
        </section>
      </div>
    </section>
  );
}
