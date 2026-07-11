import { convertFileSrc } from "@tauri-apps/api/core";
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import { openPath as open } from "@tauri-apps/plugin-opener";
import {
  pickDirectory,
  pickFiles,
  runTool,
  type AiImageArtifact,
  type AiImageConfig,
  type AiImageHistoryItem,
  type AiImageProfile,
} from "../api/tauri";
import { ActionBar, DirectoryPickerRow, RuntimeLogPanel, ToolHeading } from "../features/tools/components/CommonToolParts";
import { errorText } from "../features/tools/utils/toolResult";


type ProfileModalMode = "create" | "edit";
type SizeMode = "auto" | "ratio" | "custom";
type RatioOption = "1:1" | "3:2" | "2:3" | "16:9" | "9:16" | "4:3" | "3:4" | "21:9";
type BaseResolution = "1K" | "2K" | "4K";
type QualityOption = "auto" | "low" | "medium" | "high";
type OutputFormatOption = "png" | "jpeg" | "webp";
type BackgroundOption = "false" | "true";
type ModerationOption = "auto" | "low";
type GenerationTaskStatus = "running" | "success" | "error";

type ProfileDraft = {
  id: string;
  name: string;
  base_url: string;
  model: string;
  api_key: string;
  secret_ref: string;
  created_at: string;
  updated_at: string;
};

type GenerationTask = {
  id: string;
  title: string;
  prompt: string;
  negativePrompt: string;
  size: string;
  quality: QualityOption;
  outputFormat: OutputFormatOption;
  outputCompression: number;
  background: BackgroundOption;
  moderation: ModerationOption;
  count: number;
  status: GenerationTaskStatus;
  startedAt: number;
  finishedAt?: number;
  outputDir?: string;
  images: AiImageArtifact[];
  referenceImages: string[];
  error?: string;
};

const RATIO_PRESETS: Array<{ value: RatioOption; width: number; height: number }> = [
  { value: "1:1", width: 1, height: 1 },
  { value: "3:2", width: 3, height: 2 },
  { value: "2:3", width: 2, height: 3 },
  { value: "16:9", width: 16, height: 9 },
  { value: "9:16", width: 9, height: 16 },
  { value: "4:3", width: 4, height: 3 },
  { value: "3:4", width: 3, height: 4 },
  { value: "21:9", width: 21, height: 9 },
];

const SIZE_BY_BASE_AND_RATIO: Record<BaseResolution, Record<RatioOption, string>> = {
  "1K": {
    "1:1": "1024x1024",
    "3:2": "1536x1024",
    "2:3": "1024x1536",
    "16:9": "1280x720",
    "9:16": "720x1280",
    "4:3": "1024x768",
    "3:4": "768x1024",
    "21:9": "1920x816",
  },
  "2K": {
    "1:1": "2048x2048",
    "3:2": "2160x1440",
    "2:3": "1440x2160",
    "16:9": "2560x1440",
    "9:16": "1440x2560",
    "4:3": "2048x1536",
    "3:4": "1536x2048",
    "21:9": "3120x1344",
  },
  "4K": {
    "1:1": "2880x2880",
    "3:2": "3456x2304",
    "2:3": "2304x3456",
    "16:9": "3840x2160",
    "9:16": "2160x3840",
    "4:3": "3200x2400",
    "3:4": "2400x3200",
    "21:9": "3840x1648",
  },
};

const RATIO_SIZE_PRESETS: Record<RatioOption, string> = SIZE_BY_BASE_AND_RATIO["1K"];
const BASE_RESOLUTION_OPTIONS: BaseResolution[] = ["1K", "2K", "4K"];


function toConfig(result: unknown): AiImageConfig {
  const data = (result as { data?: AiImageConfig }).data ?? result;
  return data as AiImageConfig;
}


function toImages(result: unknown): { images: AiImageArtifact[]; outputDir: string; historyId: string } {
  const data =
    (result as { data?: { images?: AiImageArtifact[]; output_dir?: string; history_id?: string } }).data ??
    (result as { images?: AiImageArtifact[]; output_dir?: string; history_id?: string });
  return {
    images: Array.isArray(data.images) ? data.images : [],
    outputDir: typeof data.output_dir === "string" ? data.output_dir : "",
    historyId: typeof data.history_id === "string" ? data.history_id : "",
  };
}


function newProfileDraft(): ProfileDraft {
  const now = new Date().toISOString();
  return {
    id: `profile-${Date.now()}`,
    name: "",
    base_url: "",
    model: "gpt-image-2",
    api_key: "",
    secret_ref: "",
    created_at: now,
    updated_at: now,
  };
}


function draftFromProfile(profile: AiImageProfile): ProfileDraft {
  return {
    ...profile,
    api_key: "",
  };
}


function fileUrl(path: string): string {
  const normalized = path.replace(/\\/g, "/");
  const prefixed = normalized.startsWith("/") ? `file://${normalized}` : `file:///${normalized}`;
  return encodeURI(prefixed);
}


function toHistoryItems(result: unknown): AiImageHistoryItem[] {
  const data =
    (result as { data?: { items?: AiImageHistoryItem[] }; items?: AiImageHistoryItem[] }).data ??
    (result as { items?: AiImageHistoryItem[] });
  return Array.isArray(data.items) ? data.items : [];
}


function localImageSrc(path: string): string {
  if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
    return convertFileSrc(path);
  }
  return fileUrl(path);
}


function referenceImageSrc(path: string): string {
  return localImageSrc(path);
}


function filenameFromPath(path: string): string {
  return path.replace(/\\/g, "/").split("/").pop() || path;
}


function imageDetailLayout(image?: AiImageArtifact): { orientation: "portrait" | "landscape" | "square"; style: CSSProperties } {
  const width = Number(image?.width);
  const height = Number(image?.height);
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return { orientation: "square", style: {} };
  }

  const ratio = width / height;
  const orientation = ratio < 0.85 ? "portrait" : ratio > 1.2 ? "landscape" : "square";
  const mediaColumn = orientation === "portrait" ? 420 : orientation === "landscape" ? 560 : 460;
  const contentColumn = orientation === "portrait" ? 500 : 460;

  return {
    orientation,
    style: {
      "--task-detail-image-aspect": `${width} / ${height}`,
      "--task-detail-media-column": `${mediaColumn}px`,
      "--task-detail-width": `${mediaColumn + contentColumn}px`,
    } as CSSProperties,
  };
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


function gcd(a: number, b: number): number {
  let x = Math.abs(a);
  let y = Math.abs(b);
  while (y) {
    const temp = x % y;
    x = y;
    y = temp;
  }
  return x || 1;
}


function roundDownToMultiple(value: number, unit = 16): number {
  return Math.max(unit, Math.floor(value / unit) * unit);
}


function supportedSizeFromDimensions(width: number, height: number): string {
  return `${roundDownToMultiple(width)}x${roundDownToMultiple(height)}`;
}


function safeDimension(value: string, fallback: number): number {
  const number = Number(value || fallback);
  return Number.isFinite(number) ? Math.max(16, number) : fallback;
}


function sizeFromRatio(ratio: RatioOption): string {
  return RATIO_SIZE_PRESETS[ratio];
}


function sizeFromBaseAndRatio(base: BaseResolution, ratio: RatioOption): string {
  return base === "1K" ? sizeFromRatio(ratio) : SIZE_BY_BASE_AND_RATIO[base][ratio];
}


function ratioFromSize(size: string): RatioOption {
  const exact = Object.entries(RATIO_SIZE_PRESETS).find(([, value]) => value === size)?.[0];
  if (exact) {
    return exact as RatioOption;
  }
  const match = size.match(/^(\d+)x(\d+)$/);
  if (!match) {
    return "1:1";
  }
  const width = Number(match[1]);
  const height = Number(match[2]);
  const divisor = gcd(width, height);
  const normalized = `${Math.round(width / divisor)}:${Math.round(height / divisor)}`;
  return (RATIO_PRESETS.find((item) => item.value === normalized)?.value ?? "1:1") as RatioOption;
}


function sizeLabel(size: string, sizeMode: SizeMode): string {
  if (sizeMode === "auto" || size === "auto") {
    return "auto";
  }
  return size;
}


function sizePreviewFor(
  mode: SizeMode,
  base: BaseResolution,
  ratio: RatioOption,
  width: string,
  height: string,
): string {
  if (mode === "auto") {
    return "auto";
  }
  if (mode === "custom") {
    return supportedSizeFromDimensions(safeDimension(width, 1024), safeDimension(height, 1024));
  }
  return sizeFromBaseAndRatio(base, ratio);
}


function taskElapsedLabel(task: GenerationTask, now = Date.now()): string {
  const end = task.finishedAt ?? now;
  const seconds = Math.max(1, Math.round((end - task.startedAt) / 1000));
  return seconds >= 60 ? `${Math.floor(seconds / 60)}分${seconds % 60}秒` : `${seconds}秒`;
}


function taskParamSummary(task: GenerationTask): string {
  const compression = task.outputFormat === "png" ? "" : ` · 压缩 ${task.outputCompression}`;
  return `${task.size} · ${task.quality} · ${task.outputFormat}${compression} · ${task.count}张`;
}


function taskStatusLabel(task: GenerationTask, now = Date.now()): string {
  if (task.status === "running") {
    return `生成中 ${taskElapsedLabel(task, now)}`;
  }
  if (task.status === "error") {
    return task.error || "生成失败";
  }
  return `完成 ${taskElapsedLabel(task, now)}`;
}

function taskTitleFromPrompt(prompt: string): string {
  const text = prompt.trim();
  if (!text) {
    return "未命名任务";
  }
  return text.length > 24 ? `${text.slice(0, 24)}...` : text;
}


function numberFromIso(value: string | undefined): number {
  const parsed = value ? Date.parse(value) : NaN;
  return Number.isFinite(parsed) ? parsed : Date.now();
}


function historyTaskFromItem(item: AiImageHistoryItem): GenerationTask {
  const startedAt = item.startedAt ?? numberFromIso(item.created_at);
  return {
    id: item.id,
    title: item.title || taskTitleFromPrompt(item.prompt),
    prompt: item.prompt || "",
    negativePrompt: item.negativePrompt || "",
    size: item.size || "1024x1024",
    quality: (item.quality || "auto") as QualityOption,
    outputFormat: (item.outputFormat || "png") as OutputFormatOption,
    outputCompression: Number(item.outputCompression ?? 80),
    background: item.background === "transparent" || item.background === "true" ? "true" : "false",
    moderation: (item.moderation || "auto") as ModerationOption,
    count: Number(item.count || item.images?.length || 1),
    status: item.status === "error" ? "error" : "success",
    startedAt,
    finishedAt: item.finishedAt ?? startedAt,
    outputDir: item.outputDir,
    images: item.images ?? [],
    referenceImages: item.referenceImages ?? [],
    error: item.error,
  };
}


function AiImageTool() {
  const [profiles, setProfiles] = useState<AiImageProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [outputDir, setOutputDir] = useState("");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [count, setCount] = useState(1);
  const [quality, setQuality] = useState<QualityOption>("auto");
  const [outputFormat, setOutputFormat] = useState<OutputFormatOption>("png");
  const [outputCompression, setOutputCompression] = useState(80);
  const [background, setBackground] = useState<BackgroundOption>("false");
  const [moderation, setModeration] = useState<ModerationOption>("auto");
  const [referenceImages, setReferenceImages] = useState<string[]>([]);
  const [size, setSize] = useState("1024x1024");
  const [sizeMode, setSizeMode] = useState<SizeMode>("ratio");
  const [selectedRatio, setSelectedRatio] = useState<RatioOption>("1:1");
  const [selectedBaseResolution, setSelectedBaseResolution] = useState<BaseResolution>("1K");
  const [customWidth, setCustomWidth] = useState("1024");
  const [customHeight, setCustomHeight] = useState("1024");
  const [draftSizeMode, setDraftSizeMode] = useState<SizeMode>("ratio");
  const [draftSelectedRatio, setDraftSelectedRatio] = useState<RatioOption>("1:1");
  const [draftSelectedBaseResolution, setDraftSelectedBaseResolution] = useState<BaseResolution>("1K");
  const [draftCustomWidth, setDraftCustomWidth] = useState("1024");
  const [draftCustomHeight, setDraftCustomHeight] = useState("1024");
  const [isSizeModalOpen, setIsSizeModalOpen] = useState(false);
  const [images, setImages] = useState<AiImageArtifact[]>([]);
  const [generatedOutputDir, setGeneratedOutputDir] = useState("");
  const [generationTasks, setGenerationTasks] = useState<GenerationTask[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [activeGenerateCount, setActiveGenerateCount] = useState(0);
  const [elapsedNow, setElapsedNow] = useState(() => Date.now());
  const [error, setError] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [profileModalMode, setProfileModalMode] = useState<ProfileModalMode>("create");
  const [profileDraft, setProfileDraft] = useState<ProfileDraft>(newProfileDraft());

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === selectedProfileId) ?? profiles[0] ?? null,
    [profiles, selectedProfileId],
  );
  const selectedTask = useMemo(
    () => generationTasks.find((task) => task.id === selectedTaskId) ?? null,
    [generationTasks, selectedTaskId],
  );
  const sizePreview = useMemo(() => sizeLabel(size, sizeMode), [size, sizeMode]);
  const draftSizePreview = useMemo(
    () => sizePreviewFor(draftSizeMode, draftSelectedBaseResolution, draftSelectedRatio, draftCustomWidth, draftCustomHeight),
    [draftSizeMode, draftSelectedBaseResolution, draftSelectedRatio, draftCustomWidth, draftCustomHeight],
  );
  const selectedTaskImage = selectedTask?.images[0];
  const taskDetailLayout = useMemo(() => imageDetailLayout(selectedTaskImage), [selectedTaskImage]);
  const hasActiveGenerations = activeGenerateCount > 0;
  const canGenerate = Boolean(activeProfile?.id) && Boolean(prompt.trim()) && Boolean(outputDir.trim()) && count > 0;

  useEffect(() => {
    void loadConfig();
    void loadHistory();
  }, []);

  useEffect(() => {
    if (!generationTasks.some((task) => task.status === "running")) {
      return;
    }
    setElapsedNow(Date.now());
    const timer = window.setInterval(() => setElapsedNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [generationTasks]);

  async function loadConfig() {
    setLoading(true);
    setError("");
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-load-${Date.now()}`,
        action: "load_config",
        payload: {},
      });
      const config = toConfig(result);
      const nextSize = config.default_size || "1024x1024";
      setProfiles(config.profiles);
      setSelectedProfileId(config.selected_profile_id || config.profiles[0]?.id || "");
      setOutputDir(config.output_dir);
      setSize(nextSize);
      setCount(Math.max(1, Number(config.default_count || 1)));
      if (nextSize === "auto") {
        setSizeMode("auto");
      } else {
        setSizeMode("ratio");
        setSelectedRatio(ratioFromSize(nextSize));
        const match = nextSize.match(/^(\d+)x(\d+)$/);
        if (match) {
          setCustomWidth(match[1]);
          setCustomHeight(match[2]);
        }
      }
      setLogs((items) => ["已加载生图配置", ...items].slice(0, 6));
    } catch (caught) {
      setError(errorText(caught));
    } finally {
      setLoading(false);
    }
  }

  async function persistProfiles(nextProfiles: AiImageProfile[], nextSelectedProfileId: string) {
    const result = await runTool("aiimage", {
      task_id: `aiimage-save-${Date.now()}`,
      action: "save_config",
      payload: {
        selected_profile_id: nextSelectedProfileId,
        output_dir: outputDir,
        default_size: size,
        default_count: count,
        profiles: nextProfiles,
      },
    });
    const config = toConfig(result);
    setProfiles(config.profiles);
    setSelectedProfileId(config.selected_profile_id || config.profiles[0]?.id || "");
    setOutputDir(config.output_dir);
  }

  function openCreateProfileModal() {
    setProfileModalMode("create");
    setProfileDraft(newProfileDraft());
    setIsProfileModalOpen(true);
  }

  function openEditProfileModal() {
    if (!activeProfile) {
      return;
    }
    setProfileModalMode("edit");
    setProfileDraft(draftFromProfile(activeProfile));
    setIsProfileModalOpen(true);
  }

  function closeProfileModal() {
    if (!saving) {
      setIsProfileModalOpen(false);
    }
  }

  function updateProfileDraft(field: keyof ProfileDraft, value: string) {
    setProfileDraft((current) => ({ ...current, [field]: value }));
  }

  async function saveProfileModal() {
    const name = profileDraft.name.trim();
    const baseUrl = profileDraft.base_url.trim();
    const model = profileDraft.model.trim();
    if (!name || !baseUrl || !model) {
      setError("配置名称、Base URL、Model 不能为空");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const normalizedDraft = {
        ...profileDraft,
        name,
        base_url: baseUrl,
        model,
      };
      const nextProfiles =
        profileModalMode === "create"
          ? [...profiles, normalizedDraft]
          : profiles.map((profile) => (profile.id === normalizedDraft.id ? normalizedDraft : profile));
      const result = await runTool("aiimage", {
        task_id: `aiimage-save-profile-${Date.now()}`,
        action: "save_config",
        payload: {
          selected_profile_id: normalizedDraft.id,
          output_dir: outputDir,
          default_size: size,
          default_count: count,
          profiles: nextProfiles.map((profile) => ({
            ...profile,
            ...(profile.id === normalizedDraft.id && normalizedDraft.api_key.trim()
              ? { api_key: normalizedDraft.api_key.trim() }
              : {}),
          })),
        },
      });
      const config = toConfig(result);
      setProfiles(config.profiles);
      setSelectedProfileId(config.selected_profile_id || config.profiles[0]?.id || "");
      setIsProfileModalOpen(false);
      setLogs((items) => [profileModalMode === "create" ? "已新建配置" : "已更新配置", ...items].slice(0, 6));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`配置保存失败：${message}`, ...items].slice(0, 6));
    } finally {
      setSaving(false);
    }
  }

  async function deleteProfile() {
    if (!activeProfile) {
      return;
    }
    if (!window.confirm(`确定删除配置“${activeProfile.name}”吗？`)) {
      return;
    }
    setSaving(true);
    setError("");
    try {
      const nextProfiles = profiles.filter((profile) => profile.id !== activeProfile.id);
      await persistProfiles(nextProfiles, nextProfiles[0]?.id ?? "");
      setLogs((items) => ["已删除配置", ...items].slice(0, 6));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setLogs((items) => [`删除失败：${message}`, ...items].slice(0, 6));
    } finally {
      setSaving(false);
    }
  }

  function openSizeModal() {
    setDraftSizeMode(sizeMode);
    setDraftSelectedRatio(selectedRatio);
    setDraftSelectedBaseResolution(selectedBaseResolution);
    setDraftCustomWidth(customWidth);
    setDraftCustomHeight(customHeight);
    setIsSizeModalOpen(true);
  }

  async function loadHistory() {
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-history-load-${Date.now()}`,
        action: "load_history",
        payload: {},
      });
      setGenerationTasks(toHistoryItems(result).map(historyTaskFromItem));
    } catch (caught) {
      setLogs((items) => [`历史加载失败：${errorText(caught)}`, ...items].slice(0, 6));
    }
  }

  function closeSizeModal() {
    setIsSizeModalOpen(false);
  }

  function applyDraftRatioSize(nextRatio: RatioOption = draftSelectedRatio, nextBase: BaseResolution = draftSelectedBaseResolution) {
    setDraftSizeMode("ratio");
    setDraftSelectedRatio(nextRatio);
    setDraftSelectedBaseResolution(nextBase);
  }

  function confirmSizeModal() {
    if (draftSizeMode === "auto") {
      setSizeMode("auto");
      setSize("auto");
    } else if (draftSizeMode === "ratio") {
      setSizeMode("ratio");
      setSelectedRatio(draftSelectedRatio);
      setSelectedBaseResolution(draftSelectedBaseResolution);
      setSize(sizeFromBaseAndRatio(draftSelectedBaseResolution, draftSelectedRatio));
    } else {
      const width = safeDimension(draftCustomWidth, 1024);
      const height = safeDimension(draftCustomHeight, 1024);
      setSizeMode("custom");
      setCustomWidth(String(width));
      setCustomHeight(String(height));
      setSize(supportedSizeFromDimensions(width, height));
    }
    closeSizeModal();
  }

  async function chooseOutputDir() {
    const path = await pickDirectory({ title: "选择生图输出目录" });
    if (path) {
      setOutputDir(path);
    }
  }

  async function chooseReferenceImages() {
    const paths = await pickFiles({
      title: "选择参考图片",
      filters: [{ name: "Images", extensions: ["png", "jpg", "jpeg", "webp"] }],
      multiple: true,
    });
    if (paths?.length) {
      setReferenceImages((current) => Array.from(new Set([...current, ...paths])));
    }
  }

  function removeReferenceImage(path: string) {
    setReferenceImages((current) => current.filter((item) => item !== path));
  }

  async function generate() {
    if (!activeProfile || !canGenerate) {
      return;
    }
    const taskInput = {
      profileId: activeProfile.id,
      prompt: prompt.trim(),
      negativePrompt: negativePrompt.trim(),
      size,
      quality,
      outputFormat,
      outputCompression,
      background,
      moderation,
      count,
      referenceImages: [...referenceImages],
      outputDir,
    };
    const taskId = `task-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const startedAt = Date.now();
    const draftTask: GenerationTask = {
      id: taskId,
      title: taskTitleFromPrompt(taskInput.prompt),
      prompt: taskInput.prompt,
      negativePrompt: taskInput.negativePrompt,
      size: taskInput.size,
      quality: taskInput.quality,
      outputFormat: taskInput.outputFormat,
      outputCompression: taskInput.outputCompression,
      background: taskInput.background,
      moderation: taskInput.moderation,
      count: taskInput.count,
      status: "running",
      startedAt,
      images: [],
      referenceImages: taskInput.referenceImages,
    };
    setActiveGenerateCount((value) => value + 1);
    setError("");
    setGenerationTasks((items) => [draftTask, ...items]);
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-generate-${Date.now()}`,
        action: "generate",
        payload: {
          profile_id: taskInput.profileId,
          prompt: taskInput.prompt,
          negative_prompt: taskInput.negativePrompt,
          size: taskInput.size,
          n: taskInput.count,
          quality: taskInput.quality,
          output_format: taskInput.outputFormat,
          ...(taskInput.outputFormat === "png" ? {} : { output_compression: taskInput.outputCompression }),
          background: taskInput.background === "true" ? "transparent" : "auto",
          moderation: taskInput.moderation,
          reference_image_paths: taskInput.referenceImages,
          output_dir: taskInput.outputDir,
        },
      });
      const next = toImages(result);
      setImages(next.images);
      setGeneratedOutputDir(next.outputDir);
      setGenerationTasks((items) =>
        items.map((task) =>
          task.id === taskId
            ? {
                ...task,
                id: next.historyId || task.id,
                status: "success",
                images: next.images,
                outputDir: next.outputDir,
                finishedAt: Date.now(),
              }
            : task,
        ),
      );
      setLogs((items) => [`生成完成：${next.images.length} 张`, ...items].slice(0, 6));
    } catch (caught) {
      const message = errorText(caught);
      setError(message);
      setGenerationTasks((items) =>
        items.map((task) =>
          task.id === taskId
            ? {
                ...task,
                status: "error",
                error: message,
                finishedAt: Date.now(),
              }
            : task,
        ),
      );
      setLogs((items) => [`生成失败：${message}`, ...items].slice(0, 6));
    } finally {
      setActiveGenerateCount((value) => Math.max(0, value - 1));
    }
  }

  function reuseTaskConfig(task: GenerationTask) {
    setPrompt(task.prompt);
    setNegativePrompt(task.negativePrompt);
    setCount(task.count);
    setQuality(task.quality);
    setOutputFormat(task.outputFormat);
    setOutputCompression(task.outputCompression);
    setBackground(task.background);
    setModeration(task.moderation);
    setReferenceImages(task.referenceImages ?? []);
    setSize(task.size);
    if (task.size === "auto") {
      setSizeMode("auto");
    } else {
      setSizeMode("ratio");
      setSelectedRatio(ratioFromSize(task.size));
      const match = task.size.match(/^(\d+)x(\d+)$/);
      if (match) {
        setCustomWidth(match[1]);
        setCustomHeight(match[2]);
      }
    }
  }

  async function deleteTask(taskId: string) {
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-history-delete-${Date.now()}`,
        action: "delete_history",
        payload: { id: taskId },
      });
      setGenerationTasks(toHistoryItems(result).map(historyTaskFromItem));
    } catch (caught) {
      setError(errorText(caught));
      setGenerationTasks((items) => items.filter((task) => task.id !== taskId));
    }
    if (selectedTaskId === taskId) {
      setSelectedTaskId("");
    }
  }

  async function clearHistory() {
    try {
      const result = await runTool("aiimage", {
        task_id: `aiimage-history-clear-${Date.now()}`,
        action: "clear_history",
        payload: {},
      });
      setGenerationTasks(toHistoryItems(result).map(historyTaskFromItem));
      setSelectedTaskId("");
    } catch (caught) {
      setError(errorText(caught));
    }
  }

  return (
    <div className="aiimage-tool">
      <ToolHeading
        eyebrow="AI image"
        title="AI 生图"
        statusLabel={activeProfile ? activeProfile.name : "未配置"}
      />

      <section className="aiimage-studio-grid">
        <aside className="aiimage-control-rail" aria-label="AI 生图参数区">
          <section className="file-mode-card compact-card aiimage-profile-strip">
            <label className="field-block">
              <span>配置档</span>
              <select disabled={loading || saving} onChange={(event) => setSelectedProfileId(event.currentTarget.value)} value={selectedProfileId}>
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
            <div className="button-cluster aiimage-profile-actions">
              <button className="ghost-button" disabled={saving || hasActiveGenerations} onClick={openCreateProfileModal} type="button">
                新建
              </button>
              <button className="ghost-button" disabled={!activeProfile || saving || hasActiveGenerations} onClick={openEditProfileModal} type="button">
                编辑
              </button>
              <button className="ghost-button" disabled={!activeProfile || saving || hasActiveGenerations} onClick={deleteProfile} type="button">
                删除
              </button>
            </div>
          </section>

          <section className="editor-grid aiimage-main-grid aiimage-composer">
            <div className="file-mode-card compact-card prompt-main-panel">
              <label className="field-block prompt-field">
                <span>提示词</span>
                <textarea
                  onChange={(event) => setPrompt(event.currentTarget.value)}
                  placeholder="描述你想生成的图片，可输入人物、风格、镜头、光线、材质、背景、构图等信息。"
                  value={prompt}
                />
              </label>
              <div className="aiimage-reference-panel">
                <div className="aiimage-reference-head">
                  <span>参考图</span>
                  <div className="button-cluster">
                    <button className="ghost-button" onClick={chooseReferenceImages} type="button">
                      上传图片
                    </button>
                    <button className="ghost-button" disabled={!referenceImages.length} onClick={() => setReferenceImages([])} type="button">
                      清空
                    </button>
                  </div>
                </div>
                {referenceImages.length ? (
                  <div className="aiimage-reference-grid">
                    {referenceImages.map((path) => (
                      <div className="aiimage-reference-thumb" key={path}>
                        <img alt={filenameFromPath(path)} src={referenceImageSrc(path)} />
                        <button aria-label={`移除 ${filenameFromPath(path)}`} onClick={() => removeReferenceImage(path)} type="button">
                          ×
                        </button>
                        <small>{filenameFromPath(path)}</small>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>

            <div className="file-mode-card compact-card prompt-side-panel">
              <label className="field-block side-textarea-field">
                <span>负面词</span>
                <textarea
                  onChange={(event) => setNegativePrompt(event.currentTarget.value)}
                  placeholder="可选：不想要的元素"
                  value={negativePrompt}
                />
              </label>

              <div className="aiimage-param-grid">
                <div className="field-block aiimage-inline-field">
                  <span>尺寸</span>
                  <button className="aiimage-size-select" onClick={openSizeModal} type="button">
                    {sizePreview}
                  </button>
                </div>

                <label className="field-block aiimage-inline-field">
                  <span>质量</span>
                  <select onChange={(event) => setQuality(event.currentTarget.value as QualityOption)} value={quality}>
                    <option value="auto">auto</option>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                </label>

                <label className="field-block aiimage-inline-field">
                  <span>格式</span>
                  <select onChange={(event) => setOutputFormat(event.currentTarget.value as OutputFormatOption)} value={outputFormat}>
                    <option value="png">PNG</option>
                    <option value="jpeg">JPEG</option>
                    <option value="webp">WebP</option>
                  </select>
                </label>

                {outputFormat !== "png" ? (
                  <label className="field-block aiimage-inline-field aiimage-compression-field">
                    <span>压缩</span>
                    <input
                      max={100}
                      min={0}
                      onChange={(event) => setOutputCompression(Math.max(0, Math.min(100, Number(event.currentTarget.value || 0))))}
                      type="number"
                      value={outputCompression}
                    />
                  </label>
                ) : null}

                <label className="field-block aiimage-inline-field">
                  <span>透明背景</span>
                  <select onChange={(event) => setBackground(event.currentTarget.value as BackgroundOption)} value={background}>
                    <option value="false">false</option>
                    <option value="true">true</option>
                  </select>
                </label>

                <label className="field-block aiimage-inline-field">
                  <span>审核</span>
                  <select onChange={(event) => setModeration(event.currentTarget.value as ModerationOption)} value={moderation}>
                    <option value="auto">auto</option>
                    <option value="low">low</option>
                  </select>
                </label>

                <label className="field-block aiimage-inline-field">
                  <span>数量</span>
                  <input max={9} min={1} onChange={(event) => setCount(Math.max(1, Number(event.currentTarget.value || 1)))} type="number" value={count} />
                </label>
              </div>

              <DirectoryPickerRow label="输出目录" onChange={setOutputDir} onPick={chooseOutputDir} value={outputDir} />

              <div className="result-card aiimage-summary-card">
                <span>当前结果</span>
                <strong>{images.length ? `${images.length} 张` : "等待生成"}</strong>
                {generatedOutputDir ? <p>{generatedOutputDir}</p> : null}
              </div>
            </div>
          </section>

          <ActionBar
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
                {hasActiveGenerations ? `继续生图（${activeGenerateCount} 进行中）` : "开始生图"}
              </button>
            }
          />
        </aside>

        <section className="table-panel aiimage-stage">
          <div className="web-video-log-header">
            <div className="panel-title">结果画布</div>
            <button className="ghost-button" disabled={!generationTasks.length || hasActiveGenerations} onClick={() => void clearHistory()} type="button">
              清空历史
            </button>
          </div>
          {generationTasks.length ? (
            <div className="generation-history-grid">
              {generationTasks.map((task) => (
                <button className="generation-card" key={task.id} onClick={() => setSelectedTaskId(task.id)} type="button">
                  <div className="generation-card-preview">
                    {task.images[0] ? <img alt={task.title} src={localImageSrc(task.images[0].path)} /> : <div className="generation-card-placeholder">{task.status === "running" ? taskStatusLabel(task, elapsedNow) : task.status === "error" ? "失败" : "无图"}</div>}
                    <div className="generation-card-badge">
                      <span>{task.size}</span>
                    </div>
                  </div>
                  <div className="generation-card-body">
                    <strong>{task.title}</strong>
                    <small className="generation-card-status">{taskStatusLabel(task, elapsedNow)}</small>
                    <div className="aiimage-task-footer">
                      <span>{taskParamSummary(task)}</span>
                      <span>{task.images.length ? `${task.images.length} 张` : ""}</span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          ) : null}
          {images.length && !generationTasks.length ? (
            <div className="image-grid">
              {images.map((image) => (
                <article className="image-card" key={image.path}>
                  <button className="image-preview-button" onClick={() => void open(image.path)} type="button">
                    <img alt={image.filename} src={localImageSrc(image.path)} />
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
          ) : (
            <div className="aiimage-empty-state">
              <strong>输入提示词开始生成图片</strong>
            </div>
          )}
        </section>
      </section>

      <RuntimeLogPanel error={error} logs={logs} />

      {isProfileModalOpen ? createPortal((
        <div className="modal-scrim profile-modal" onClick={closeProfileModal}>
          <div className="profile-modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="tool-heading profile-modal-head">
              <div>
                <h2>{profileModalMode === "create" ? "新建配置" : "编辑配置"}</h2>
              </div>
            </div>

            <div className="mini-form-grid profile-modal-grid">
              <label className="field-block">
                <span>配置名称</span>
                <input onChange={(event) => updateProfileDraft("name", event.currentTarget.value)} value={profileDraft.name} />
              </label>
              <label className="field-block">
                <span>Model</span>
                <input onChange={(event) => updateProfileDraft("model", event.currentTarget.value)} value={profileDraft.model} />
              </label>
              <label className="field-block profile-modal-wide">
                <span>Base URL</span>
                <input onChange={(event) => updateProfileDraft("base_url", event.currentTarget.value)} placeholder="https://api.openai.com/v1" value={profileDraft.base_url} />
              </label>
              <label className="field-block profile-modal-wide">
                <span>API Key</span>
                <input
                  onChange={(event) => updateProfileDraft("api_key", event.currentTarget.value)}
                  placeholder={profileModalMode === "edit" ? "留空表示不改已保存密钥" : "输入该配置的 API Key"}
                  type="password"
                  value={profileDraft.api_key}
                />
              </label>
            </div>

            <div className="button-cluster profile-modal-actions">
              <button className="ghost-button" disabled={saving} onClick={closeProfileModal} type="button">
                取消
              </button>
              <button className="primary-button" disabled={saving} onClick={saveProfileModal} type="button">
                {saving ? "保存中" : "保存配置"}
              </button>
            </div>
          </div>
        </div>
      ), document.body) : null}

      {isSizeModalOpen ? createPortal((
        <div className="modal-scrim size-modal" onClick={closeSizeModal}>
          <div className="size-modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="size-modal-head">
              <div>
                <h3>设置图像尺寸</h3>
                <p>当前：{sizePreview}</p>
              </div>
              <button className="ghost-button size-close-button" onClick={closeSizeModal} type="button">
                ×
              </button>
            </div>

            <div className="size-mode-tabs">
              <button className={draftSizeMode === "auto" ? "active" : ""} onClick={() => setDraftSizeMode("auto")} type="button">
                自动
              </button>
              <button className={draftSizeMode === "ratio" ? "active" : ""} onClick={() => setDraftSizeMode("ratio")} type="button">
                按比例
              </button>
              <button className={draftSizeMode === "custom" ? "active" : ""} onClick={() => setDraftSizeMode("custom")} type="button">
                自定义宽高
              </button>
            </div>

            {draftSizeMode === "auto" ? (
              <div className="size-mode-body size-mode-auto">
                <div className="empty-orb" aria-hidden="true" />
                <strong>自动尺寸</strong>
              </div>
            ) : null}

            {draftSizeMode === "ratio" ? (
              <div className="size-mode-body">
                <div className="size-section">
                  <span>基准分辨率</span>
                  <div className="size-chip-grid size-base-grid">
                    {BASE_RESOLUTION_OPTIONS.map((base) => (
                      <button
                        className={draftSelectedBaseResolution === base ? "active" : ""}
                        key={base}
                        onClick={() => applyDraftRatioSize(draftSelectedRatio, base)}
                        type="button"
                      >
                        {base}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="size-section">
                  <span>图像比例</span>
                  <div className="size-chip-grid size-ratio-grid">
                    {RATIO_PRESETS.map((preset) => (
                      <button
                        className={draftSelectedRatio === preset.value ? "active" : ""}
                        key={preset.value}
                        onClick={() => applyDraftRatioSize(preset.value, draftSelectedBaseResolution)}
                        type="button"
                      >
                        {preset.value}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : null}

            {draftSizeMode === "custom" ? (
              <div className="size-mode-body">
                <div className="size-custom-grid">
                  <label className="field-block">
                    <span>宽度 (Width)</span>
                    <input
                      onChange={(event) => {
                        setDraftCustomWidth(event.currentTarget.value);
                        setDraftSizeMode("custom");
                      }}
                      type="number"
                      value={draftCustomWidth}
                    />
                  </label>
                  <label className="field-block">
                    <span>高度 (Height)</span>
                    <input
                      onChange={(event) => {
                        setDraftCustomHeight(event.currentTarget.value);
                        setDraftSizeMode("custom");
                      }}
                      type="number"
                      value={draftCustomHeight}
                    />
                  </label>
                </div>
                <div className="info-box size-note">
                  宽高建议保持 16 的倍数，模型可能会自动调整到可接受尺寸。
                </div>
              </div>
            ) : null}

            <div className="result-card size-preview-card">
              <span>将使用</span>
              <strong>{draftSizePreview}</strong>
            </div>

            <div className="button-cluster profile-modal-actions">
              <button className="ghost-button" onClick={closeSizeModal} type="button">
                取消
              </button>
              <button className="primary-button" onClick={confirmSizeModal} type="button">
                确定
              </button>
            </div>
          </div>
        </div>
      ), document.body) : null}

      {selectedTask ? createPortal((
        <div className="modal-scrim task-detail-modal" onClick={() => setSelectedTaskId("")}>
          <div className="task-detail-card" data-image-orientation={taskDetailLayout.orientation} onClick={(event) => event.stopPropagation()} style={taskDetailLayout.style}>
            <div className="task-detail-media">
              {selectedTaskImage ? <img alt={selectedTask.title} src={localImageSrc(selectedTaskImage.path)} /> : <div className="generation-card-placeholder">{selectedTask.status === "running" ? taskStatusLabel(selectedTask, elapsedNow) : selectedTask.status === "error" ? "失败" : "无图"}</div>}
            </div>
            <div className="task-detail-content">
              <div className="size-modal-head">
                <div>
                  <h3>{selectedTask.title}</h3>
                  {selectedTask.status !== "success" ? (
                    <p>{selectedTask.status === "running" ? taskStatusLabel(selectedTask, elapsedNow) : selectedTask.error || "生成失败"}</p>
                  ) : null}
                </div>
                <button className="ghost-button size-close-button" onClick={() => setSelectedTaskId("")} type="button">
                  ×
                </button>
              </div>

              <div className="result-card">
                <span>输入内容</span>
                <p>{selectedTask.prompt}</p>
              </div>

              {selectedTask.referenceImages.length ? (
                <div className="result-card task-reference-card">
                  <span>参考图</span>
                  <div className="task-reference-list">
                    {selectedTask.referenceImages.map((path) => (
                      <button className="task-reference-item" key={path} onClick={() => void open(path)} type="button">
                        <img alt={filenameFromPath(path)} src={referenceImageSrc(path)} />
                        <strong>{filenameFromPath(path)}</strong>
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="aiimage-task-meta-grid">
                <div className="result-card"><span>尺寸</span><strong>{selectedTask.size}</strong></div>
                <div className="result-card"><span>质量</span><strong>{selectedTask.quality}</strong></div>
                <div className="result-card"><span>格式</span><strong>{selectedTask.outputFormat}</strong></div>
                <div className="result-card"><span>压缩</span><strong>{selectedTask.outputFormat === "png" ? "-" : selectedTask.outputCompression}</strong></div>
                <div className="result-card"><span>耗时</span><strong>{taskElapsedLabel(selectedTask, elapsedNow)}</strong></div>
                <div className="result-card"><span>透明背景</span><strong>{selectedTask.background}</strong></div>
                <div className="result-card"><span>审核</span><strong>{selectedTask.moderation}</strong></div>
                <div className="result-card"><span>数量</span><strong>{selectedTask.count}</strong></div>
              </div>

              <div className="button-cluster profile-modal-actions">
                <button className="ghost-button" onClick={() => reuseTaskConfig(selectedTask)} type="button">
                  复用配置
                </button>
                <button className="ghost-button" disabled={!selectedTask.outputDir} onClick={() => selectedTask.outputDir && void open(selectedTask.outputDir)} type="button">
                  打开目录
                </button>
                <button className="ghost-button" onClick={() => void deleteTask(selectedTask.id)} type="button">
                  删除任务
                </button>
              </div>
            </div>
          </div>
        </div>
      ), document.body) : null}
    </div>
  );
}


export default AiImageTool;
