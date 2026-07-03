import { useEffect, useMemo, useState } from "react";
import { openPath as open } from "@tauri-apps/plugin-opener";
import {
  pickDirectory,
  runTool,
  type AiImageArtifact,
  type AiImageConfig,
  type AiImageProfile,
} from "../api/tauri";
import { ActionBar, DirectoryPickerRow, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { errorText } from "../features/tools/utils/toolResult";


const SIZE_OPTIONS = ["1024x1024", "1536x1024", "1024x1536"];


function emptyProfile(id: string): AiImageProfile {
  const now = new Date().toISOString();
  return {
    id,
    name: "新配置",
    base_url: "",
    model: "gpt-image-1",
    secret_ref: "",
    created_at: now,
    updated_at: now,
  };
}


function fileUrl(path: string): string {
  const normalized = path.replace(/\\/g, "/");
  const prefixed = normalized.startsWith("/") ? `file://${normalized}` : `file:///${normalized}`;
  return encodeURI(prefixed);
}


function downloadImage(image: AiImageArtifact) {
  const anchor = document.createElement("a");
  anchor.href = fileUrl(image.path);
  anchor.download = image.filename;
  anchor.click();
}


function downloadAllImages(images: readonly AiImageArtifact[]) {
  images.forEach((image, index) => {
    window.setTimeout(() => downloadImage(image), index * 120);
  });
}


function configOf(result: unknown): AiImageConfig {
  const data = (result as { data?: AiImageConfig }).data ?? result;
  return data as AiImageConfig;
}


function imagesOf(result: unknown): { images: AiImageArtifact[]; outputDir: string } {
  const data = (result as { data?: { images?: AiImageArtifact[]; output_dir?: string } }).data ?? (result as { images?: AiImageArtifact[]; output_dir?: string });
  return {
    images: Array.isArray(data.images) ? data.images : [],
    outputDir: typeof data.output_dir === "string" ? data.output_dir : "",
  };
}


function AiImageTool() {
  const [profiles, setProfiles] = useState<AiImageProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [size, setSize] = useState("1024x1024");
  const [count, setCount] = useState(1);
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [apiKeyDraft, setApiKeyDraft] = useState("");
  const [images, setImages] = useState<AiImageArtifact[]>([]);
  const [generatedOutputDir, setGeneratedOutputDir] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === selectedProfileId) ?? profiles[0] ?? null,
    [profiles, selectedProfileId],
  );
  const canSave = !saving && !loading && Boolean(activeProfile);
  const canGenerate =
    !running && Boolean(activeProfile?.id) && Boolean(prompt.trim()) && Boolean(outputDir.trim()) && Boolean(size.trim()) && count > 0;

  useEffect(() => {
    void loadConfig();
  }, []);

  async function loadConfig() {
    setLoading(true);
    setError("");
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-load-${Date.now()}`,
        action: "load_config",
        payload: {},
      });
      const config = configOf(result);
      setProfiles(config.profiles);
      setSelectedProfileId(config.selected_profile_id || config.profiles[0]?.id || "");
      setOutputDir(config.output_dir);
      setSize(config.default_size);
      setCount(Math.max(1, Number(config.default_count || 1)));
      setLogs((items) => ["已加载 AI 生图配置", ...items].slice(0, 6));
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setLoading(false);
    }
  }

  function updateProfile(field: keyof AiImageProfile, value: string) {
    if (!activeProfile) {
      return;
    }
    setProfiles((items) =>
      items.map((profile) => (profile.id === activeProfile.id ? { ...profile, [field]: value } : profile)),
    );
  }

  function addProfile() {
    const id = `profile-${Date.now()}`;
    const profile = emptyProfile(id);
    setProfiles((items) => [...items, profile]);
    setSelectedProfileId(id);
    setApiKeyDraft("");
  }

  function removeProfile() {
    if (!activeProfile) {
      return;
    }
    const nextProfiles = profiles.filter((profile) => profile.id !== activeProfile.id);
    setProfiles(nextProfiles);
    setSelectedProfileId(nextProfiles[0]?.id ?? "");
    setApiKeyDraft("");
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择 AI 生图输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  async function saveConfig() {
    if (!activeProfile || !canSave) {
      return;
    }
    setSaving(true);
    setError("");
    try {
      const payloadProfiles = profiles.map((profile) => ({
        ...profile,
        ...(profile.id === activeProfile.id && apiKeyDraft.trim() ? { api_key: apiKeyDraft.trim() } : {}),
      }));
      const result = await runTool("aiimage", {
        task_id: `aiimage-save-${Date.now()}`,
        action: "save_config",
        payload: {
          selected_profile_id: selectedProfileId,
          output_dir: outputDir,
          default_size: size,
          default_count: count,
          profiles: payloadProfiles,
        },
      });
      const config = configOf(result);
      setProfiles(config.profiles);
      setSelectedProfileId(config.selected_profile_id || config.profiles[0]?.id || "");
      setOutputDir(config.output_dir);
      setSize(config.default_size);
      setCount(Math.max(1, Number(config.default_count || 1)));
      setApiKeyDraft("");
      setLogs((items) => ["已保存 AI 生图配置", ...items].slice(0, 6));
    } catch (caught) {
      setError(errorText(caught));
      setLogs((items) => [`保存失败：${errorText(caught)}`, ...items].slice(0, 6));
    } finally {
      setSaving(false);
    }
  }

  async function generate() {
    if (!activeProfile || !canGenerate) {
      return;
    }
    setRunning(true);
    setError("");
    setImages([]);
    setGeneratedOutputDir("");
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-generate-${Date.now()}`,
        action: "generate",
        payload: {
          profile_id: activeProfile.id,
          prompt: prompt.trim(),
          negative_prompt: negativePrompt.trim(),
          size,
          n: count,
          output_dir: outputDir,
        },
      });
      const next = imagesOf(result);
      setImages(next.images);
      setGeneratedOutputDir(next.outputDir);
      setLogs((items) => [`生成完成：${next.images.length} 张`, ...items].slice(0, 6));
    } catch (caught) {
      setError(errorText(caught));
      setLogs((items) => [`生成失败：${errorText(caught)}`, ...items].slice(0, 6));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="aiimage-tool">
      <ToolHeading
        eyebrow="AI image"
        title="AI 生图"
        description="保存多套 OpenAI 兼容生图配置，输入提示词后直接生成并下载结果。"
        statusLabel={activeProfile ? activeProfile.name : "未配置"}
      />

      <div className="file-mode-card compact-card aiimage-profile-card">
        <label className="field-block">
          <span>配置档</span>
          <select disabled={loading || saving || running} onChange={(event) => setSelectedProfileId(event.currentTarget.value)} value={selectedProfileId}>
            {profiles.length ? (
              profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))
            ) : (
              <option value="">暂无配置</option>
            )}
          </select>
        </label>
        <div className="button-cluster">
          <button className="ghost-button" disabled={saving || running} onClick={addProfile} type="button">
            新建
          </button>
          <button className="ghost-button" disabled={!activeProfile || saving || running} onClick={removeProfile} type="button">
            删除
          </button>
          <button className="primary-button" disabled={!canSave} onClick={saveConfig} type="button">
            {saving ? "保存中" : "保存配置"}
          </button>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>配置档名称</span>
            <input disabled={!activeProfile || saving || running} onChange={(event) => updateProfile("name", event.currentTarget.value)} value={activeProfile?.name ?? ""} />
          </label>
          <label className="field-block">
            <span>Base URL</span>
            <input disabled={!activeProfile || saving || running} onChange={(event) => updateProfile("base_url", event.currentTarget.value)} placeholder="https://api.openai.com/v1" value={activeProfile?.base_url ?? ""} />
          </label>
          <label className="field-block">
            <span>Model</span>
            <input disabled={!activeProfile || saving || running} onChange={(event) => updateProfile("model", event.currentTarget.value)} value={activeProfile?.model ?? "gpt-image-1"} />
          </label>
          <label className="field-block">
            <span>API Key</span>
            <input disabled={!activeProfile || saving || running} onChange={(event) => setApiKeyDraft(event.currentTarget.value)} placeholder="留空表示不修改已保存密钥" type="password" value={apiKeyDraft} />
          </label>
        </div>

        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>提示词</span>
            <textarea disabled={running} onChange={(event) => setPrompt(event.currentTarget.value)} placeholder="描述你想生成的画面" value={prompt} />
          </label>
          <label className="field-block">
            <span>负面词</span>
            <textarea disabled={running} onChange={(event) => setNegativePrompt(event.currentTarget.value)} placeholder="可选：不想要的元素" value={negativePrompt} />
          </label>
        </div>
      </div>

      <div className="editor-grid file-editor-grid">
        <div className="file-mode-card compact-card">
          <label className="field-block">
            <span>尺寸</span>
            <select disabled={running} onChange={(event) => setSize(event.currentTarget.value)} value={size}>
              {SIZE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="field-block">
            <span>张数</span>
            <input
              disabled={running}
              max={9}
              min={1}
              onChange={(event) => setCount(Math.max(1, Number(event.currentTarget.value || 1)))}
              type="number"
              value={count}
            />
          </label>
          <DirectoryPickerRow
            disabled={running}
            label="输出目录"
            onChange={setOutputDir}
            onPick={chooseOutputDir}
            value={outputDir}
          />
        </div>

        <div className="result-card">
          <span>当前结果</span>
          <strong>{images.length ? `${images.length} 张` : "等待生成"}</strong>
          <p>{generatedOutputDir || "生成成功后会保存到时间戳子目录"}</p>
        </div>
      </div>

      <ActionBar
        hint="先保存配置，再生成图片。下载按钮仅导出本地已落盘结果。"
        secondary={
          <button className="ghost-button" disabled={!generatedOutputDir} onClick={() => void open(generatedOutputDir)} type="button">
            打开输出目录
          </button>
        }
        tertiary={
          <button className="ghost-button" disabled={!images.length} onClick={() => downloadAllImages(images)} type="button">
            全部导出
          </button>
        }
        primary={
          <button className="primary-button" disabled={!canGenerate} onClick={generate} type="button">
            {running ? "生成中" : "开始生图"}
          </button>
        }
      />

      {images.length ? (
        <section className="table-panel">
          <div className="panel-title">生成结果</div>
          <div className="image-grid">
            {images.map((image) => (
              <article className="image-card" key={image.path}>
                <button className="image-preview-button" onClick={() => void open(image.path)} type="button">
                  <img alt={image.filename} src={fileUrl(image.path)} />
                </button>
                <div className="image-card-meta">
                  <strong>{image.filename}</strong>
                  <small>
                    {image.width ?? "?"} × {image.height ?? "?"}
                  </small>
                </div>
                <div className="button-cluster">
                  <button className="ghost-button" onClick={() => downloadImage(image)} type="button">
                    下载
                  </button>
                  <button className="ghost-button" onClick={() => void open(image.path)} type="button">
                    打开
                  </button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <RuntimeLogPanel error={error} logs={logs} />
    </div>
  );
}


export default AiImageTool;
