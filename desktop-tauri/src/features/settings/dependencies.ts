import type { ToolResult } from "../../api/tauri";

export type DependencyProbeStatus = {
  available: boolean;
  detail: string;
};

export type DependencyDefinition = {
  id: string;
  label: string;
  toolId: string;
  probeAction: string;
  relatedTools: readonly string[];
  readProbe: (result: ToolResult) => DependencyProbeStatus;
};

type BackendProbe = {
  available?: boolean;
  path?: string;
  message?: string;
};

type ProbeShape = ToolResult["data"] & {
  available?: boolean;
  message?: string;
  path?: string;
  backends?: Record<string, BackendProbe>;
};

function probeData(result: ToolResult): ProbeShape {
  return (result.data ?? result) as ProbeShape;
}

function explicitDetail(data: ProbeShape, availableLabel: string, missingLabel: string): string {
  const path = typeof data.path === "string" ? data.path.trim() : "";
  if (path) {
    return path;
  }
  const message = typeof data.message === "string" ? data.message.trim() : "";
  if (message) {
    return message;
  }
  return data.available ? availableLabel : missingLabel;
}

function directAvailability(label: string, missingLabel: string = `缺少 ${label}`) {
  return (result: ToolResult): DependencyProbeStatus => {
    const data = probeData(result);
    const available = Boolean(data.available);
    return {
      available,
      detail: explicitDetail(data, `${label} 可用`, missingLabel),
    };
  };
}

function backendAvailability(backendKey: string, label: string) {
  return (result: ToolResult): DependencyProbeStatus => {
    const data = probeData(result);
    const backend = data.backends?.[backendKey];
    if (!backend) {
      return {
        available: false,
        detail: `未返回 ${label} 检测结果`,
      };
    }
    const path = typeof backend.path === "string" ? backend.path.trim() : "";
    const message = typeof backend.message === "string" ? backend.message.trim() : "";
    return {
      available: Boolean(backend.available),
      detail: path || message || (backend.available ? `${label} 可用` : `缺少 ${label}`),
    };
  };
}

export const DEPENDENCY_DEFINITIONS: readonly DependencyDefinition[] = [
  {
    id: "ffmpeg",
    label: "ffmpeg",
    toolId: "mp4mp3",
    probeAction: "probe",
    relatedTools: ["MP4 转 MP3", "网页视频下载"],
    readProbe: directAvailability("ffmpeg"),
  },
  {
    id: "imagemagick",
    label: "ImageMagick",
    toolId: "imageconvert",
    probeAction: "probe",
    relatedTools: ["图片格式互转"],
    readProbe: directAvailability("ImageMagick"),
  },
  {
    id: "ncm_backend",
    label: "NCM 转换后端",
    toolId: "music",
    probeAction: "probe",
    relatedTools: ["NCM 转 MP3"],
    readProbe: directAvailability("NCM 转换后端", "缺少 NCM 转换依赖"),
  },
  {
    id: "aria2c",
    label: "aria2c",
    toolId: "directdownloader",
    probeAction: "probe",
    relatedTools: ["直接下载", "网页视频下载"],
    readProbe: directAvailability("aria2c"),
  },
  {
    id: "tesseract_ocr",
    label: "Tesseract OCR",
    toolId: "pdftools",
    probeAction: "probe_ocr",
    relatedTools: ["PDF 工具"],
    readProbe: directAvailability("Tesseract OCR", "缺少 OCR 依赖"),
  },
  {
    id: "yt_dlp",
    label: "yt-dlp",
    toolId: "webvideodownloader",
    probeAction: "probe",
    relatedTools: ["网页视频下载"],
    readProbe: backendAvailability("yt_dlp", "yt-dlp"),
  },
  {
    id: "telethon",
    label: "Telethon",
    toolId: "tgdownloader",
    probeAction: "probe",
    relatedTools: ["Telegram 下载"],
    readProbe: backendAvailability("telethon", "Telethon"),
  },
] as const;
