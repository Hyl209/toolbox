import { type DownloaderSettingsDraft } from "..";
import { SettingOutputDirRow, SettingSelectField, SettingTextField, SettingToggleRow } from "./primitives";

type DownloaderSettingsSectionProps = {
  saving: boolean;
  downloader: DownloaderSettingsDraft;
  onChange: <T extends keyof DownloaderSettingsDraft, K extends keyof DownloaderSettingsDraft[T]>(
    toolId: T,
    key: K,
    value: DownloaderSettingsDraft[T][K],
  ) => void;
};

const CONCURRENT_OPTIONS = ["0", "1", "2", "3", "4", "5"].map((value) => ({
  label: value === "0" ? "自动" : value,
  value,
}));

export default function DownloaderSettingsSection({ saving, downloader, onChange }: DownloaderSettingsSectionProps) {
  return (
    <section className="settings-card settings-wide-card">
      <span>下载器设置</span>
      <p>按使用场景拆分 Web 与 Telegram 两套设置，同时保留对旧版 `video_downloader/*` 配置的回写兼容。</p>

      <div className="settings-group-stack">
        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>Web 下载</strong>
            <p>面向网页视频下载，常用项优先展示，兼容字段收起到次级说明里。</p>
          </header>
          <div className="settings-group-stack">
            <SettingOutputDirRow
              description="用于保存网页视频下载结果。"
              disabled={saving}
              label="Web 输出目录"
              onChange={(value) => onChange("webvideodownloader", "output_dir", value)}
              pathKey="video_downloader/web/output_dir"
              value={downloader.webvideodownloader.output_dir}
            />
            <div className="settings-two-column-grid">
              <SettingTextField
                description="优先使用主机 + 端口组合。"
                disabled={saving}
                label="代理主机"
                meta="video_downloader/web/proxy_host"
                onChange={(value) => onChange("webvideodownloader", "proxy_host", value)}
                placeholder="127.0.0.1"
                value={downloader.webvideodownloader.proxy_host}
              />
              <SettingTextField
                disabled={saving}
                label="代理端口"
                meta="video_downloader/web/proxy_port"
                onChange={(value) => onChange("webvideodownloader", "proxy_port", value)}
                placeholder="7890"
                value={downloader.webvideodownloader.proxy_port}
              />
              <SettingTextField
                description="仅用于兼容旧版代理写法。"
                disabled={saving}
                label="兼容代理 URL"
                meta="video_downloader/web/proxy_url"
                onChange={(value) => onChange("webvideodownloader", "proxy_url", value)}
                placeholder="http://127.0.0.1:7890"
                value={downloader.webvideodownloader.proxy_url}
              />
              <SettingSelectField
                disabled={saving}
                label="并发下载数"
                meta="video_downloader/web/concurrent"
                onChange={(value) => onChange("webvideodownloader", "concurrent", value)}
                options={CONCURRENT_OPTIONS}
                value={downloader.webvideodownloader.concurrent}
              />
            </div>
            <div className="settings-toggle-grid">
              <SettingToggleRow
                checked={downloader.webvideodownloader.overwrite}
                description="下载前允许覆盖同名文件。"
                disabled={saving}
                label="覆盖已存在文件"
                meta="video_downloader/web/overwrite"
                onChange={(checked) => onChange("webvideodownloader", "overwrite", checked)}
              />
              <SettingToggleRow
                checked={downloader.webvideodownloader.output_subdir_by_title}
                description="按视频标题创建子目录，减少文件混放。"
                disabled={saving}
                label="按标题创建子目录"
                meta="video_downloader/web/output_subdir_by_title"
                onChange={(checked) => onChange("webvideodownloader", "output_subdir_by_title", checked)}
              />
            </div>
          </div>
        </section>

        <section className="settings-group-card">
          <header className="settings-subsection-head">
            <strong>Telegram 下载</strong>
            <p>把账号凭据、时间范围、代理与下载行为拆开，避免一行堆太多字段。</p>
          </header>
          <div className="settings-group-stack">
            <div className="settings-two-column-grid">
              <SettingTextField
                disabled={saving}
                label="API ID"
                meta="video_downloader/api_id"
                onChange={(value) => onChange("tgdownloader", "api_id", value)}
                value={downloader.tgdownloader.api_id}
              />
              <SettingTextField
                disabled={saving}
                label="API Hash"
                meta="video_downloader/api_hash"
                onChange={(value) => onChange("tgdownloader", "api_hash", value)}
                value={downloader.tgdownloader.api_hash}
              />
              <SettingTextField
                disabled={saving}
                label="手机号"
                meta="video_downloader/phone"
                onChange={(value) => onChange("tgdownloader", "phone", value)}
                value={downloader.tgdownloader.phone}
              />
              <SettingOutputDirRow
                disabled={saving}
                label="Telegram 输出目录"
                onChange={(value) => onChange("tgdownloader", "output_dir", value)}
                pathKey="video_downloader/telegram/output_dir"
                value={downloader.tgdownloader.output_dir}
              />
              <SettingTextField
                disabled={saving}
                label="最近消息数"
                meta="video_downloader/telegram/recent_limit"
                onChange={(value) => onChange("tgdownloader", "recent_limit", value)}
                value={downloader.tgdownloader.recent_limit}
              />
              <SettingSelectField
                disabled={saving}
                label="并发下载数"
                meta="video_downloader/telegram/concurrent"
                onChange={(value) => onChange("tgdownloader", "concurrent", value)}
                options={CONCURRENT_OPTIONS}
                value={downloader.tgdownloader.concurrent}
              />
              <SettingTextField
                disabled={saving}
                label="起始日期"
                meta="video_downloader/telegram/date_from"
                onChange={(value) => onChange("tgdownloader", "date_from", value)}
                placeholder="2026-07-01"
                value={downloader.tgdownloader.date_from}
              />
              <SettingTextField
                disabled={saving}
                label="结束日期"
                meta="video_downloader/telegram/date_to"
                onChange={(value) => onChange("tgdownloader", "date_to", value)}
                placeholder="2026-07-31"
                value={downloader.tgdownloader.date_to}
              />
              <SettingTextField
                disabled={saving}
                label="代理主机"
                meta="video_downloader/telegram/proxy_host"
                onChange={(value) => onChange("tgdownloader", "proxy_host", value)}
                placeholder="127.0.0.1"
                value={downloader.tgdownloader.proxy_host}
              />
              <SettingTextField
                disabled={saving}
                label="代理端口"
                meta="video_downloader/telegram/proxy_port"
                onChange={(value) => onChange("tgdownloader", "proxy_port", value)}
                placeholder="7890"
                value={downloader.tgdownloader.proxy_port}
              />
              <SettingTextField
                description="仅用于兼容旧版代理写法。"
                disabled={saving}
                label="兼容代理 URL"
                meta="video_downloader/telegram/proxy_url"
                onChange={(value) => onChange("tgdownloader", "proxy_url", value)}
                placeholder="http://127.0.0.1:7890"
                value={downloader.tgdownloader.proxy_url}
              />
            </div>
            <div className="settings-toggle-grid">
              {[
                ["all_messages", "抓取全部消息", "忽略 recent limit，只按日期范围筛选。"],
                ["include_videos", "包含视频", "下载视频消息。"],
                ["include_photos", "包含图片", "下载图片消息。"],
                ["overwrite", "覆盖已存在文件", "保存前允许覆盖同名文件。"],
                ["output_subdir_by_title", "按标题创建子目录", "按频道或消息标题整理输出目录。"],
              ].map(([key, label, description]) => (
                <SettingToggleRow
                  checked={Boolean(downloader.tgdownloader[key as keyof typeof downloader.tgdownloader])}
                  description={description}
                  disabled={saving}
                  key={key}
                  label={label}
                  meta={`video_downloader/telegram/${key}`}
                  onChange={(checked) => onChange("tgdownloader", key as keyof typeof downloader.tgdownloader, checked as never)}
                />
              ))}
            </div>
          </div>
        </section>
      </div>
    </section>
  );
}
