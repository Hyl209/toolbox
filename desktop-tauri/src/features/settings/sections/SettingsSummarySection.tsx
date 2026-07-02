type SettingsSummarySectionProps = {
  loading: boolean;
  modeText: string;
  settingsPath?: string;
  enabledTools: number;
  disabledToolsCount: number;
  disabledPluginCount: number;
  sidebarOrderCount: number;
  error: string;
  notice: string;
};

export default function SettingsSummarySection({
  loading,
  modeText,
  settingsPath,
  enabledTools,
  disabledToolsCount,
  disabledPluginCount,
  sidebarOrderCount,
  error,
  notice,
}: SettingsSummarySectionProps) {
  return (
    <section className="settings-group-stack">
      {error ? <div className="error-box">{error}</div> : null}
      {notice ? <div className="info-box">{notice}</div> : null}

      <div className="settings-grid">
        <section className="settings-card">
          <span>主题来源</span>
          <strong>{loading ? "读取中" : modeText}</strong>
          <p>{settingsPath ?? "browser-preview"}</p>
        </section>
        <section className="settings-card">
          <span>功能状态</span>
          <strong>{enabledTools} 个启用</strong>
          <p>{disabledToolsCount} 个内置工具禁用，{disabledPluginCount} 个插件禁用。</p>
        </section>
        <section className="settings-card">
          <span>侧栏顺序</span>
          <strong>{sidebarOrderCount} 条顺序记录</strong>
          <p>保存时会把旧版 `sidebar/order` 与当前可见入口合并。</p>
        </section>
      </div>
    </section>
  );
}
