import type { ReactNode } from "react";
import type { SettingsSnapshot } from "../../api/tauri";
import ArchiveExtractorPluginTool from "../../tools/ArchiveExtractorPluginTool";
import AiImageTool from "../../tools/AiImageTool";
import Base64Tool from "../../tools/Base64Tool";
import BatchRenameTool from "../../tools/BatchRenameTool";
import CsvToolsPluginTool from "../../tools/CsvToolsPluginTool";
import DirectDownloaderTool from "../../tools/DirectDownloaderTool";
import FileHasherPluginTool from "../../tools/FileHasherPluginTool";
import FileSorterTool from "../../tools/FileSorterTool";
import ImageConvertTool from "../../tools/ImageConvertTool";
import JsonToolsPluginTool from "../../tools/JsonToolsPluginTool";
import Mp4Mp3Tool from "../../tools/Mp4Mp3Tool";
import MusicTool from "../../tools/MusicTool";
import PdfToolsTool from "../../tools/PdfToolsTool";
import RegexToolsPluginTool from "../../tools/RegexToolsPluginTool";
import SameTool from "../../tools/SameTool";
import TextToolsPluginTool from "../../tools/TextToolsPluginTool";
import TgDownloaderTool from "../../tools/TgDownloaderTool";
import TimestampToolsPluginTool from "../../tools/TimestampToolsPluginTool";
import UrlToolsPluginTool from "../../tools/UrlToolsPluginTool";
import UuidToolsPluginTool from "../../tools/UuidToolsPluginTool";
import WebVideoDownloaderTool from "../../tools/WebVideoDownloaderTool";
import WordFormatterTool from "../../tools/WordFormatterTool";
import ZipPngTool from "../../tools/ZipPngTool";
import {
  downloaderSettings,
  toolBehaviorSettings,
  toolOutputDir,
  wordFormatterSettings,
} from "../settings";

type PanelRenderer = (snapshot: SettingsSnapshot | null) => ReactNode;

export const builtinPanelRenderers: Record<string, PanelRenderer> = {
  aiimage: () => <AiImageTool />,
  music: (snapshot) => <MusicTool initialOutputDir={toolOutputDir(snapshot, "music")} />,
  imageconvert: (snapshot) => <ImageConvertTool initialOutputDir={toolOutputDir(snapshot, "imageconvert")} />,
  mp4mp3: (snapshot) => <Mp4Mp3Tool initialOutputDir={toolOutputDir(snapshot, "mp4mp3")} />,
  pdftools: (snapshot) => <PdfToolsTool initialOutputDir={toolOutputDir(snapshot, "pdftools")} />,
  batchrename: (snapshot) => <BatchRenameTool initialSettings={toolBehaviorSettings(snapshot, "batchrename")} />,
  filesorter: (snapshot) => <FileSorterTool initialSettings={toolBehaviorSettings(snapshot, "filesorter")} />,
  same: (snapshot) => <SameTool initialSettings={toolBehaviorSettings(snapshot, "same")} />,
  wordformatter: (snapshot) => <WordFormatterTool initialSettings={wordFormatterSettings(snapshot)} />,
  base64: (snapshot) => <Base64Tool initialOutputDir={toolOutputDir(snapshot, "base64")} />,
  directdownloader: (snapshot) => (
    <DirectDownloaderTool
      initialOutputDir={toolOutputDir(snapshot, "directdownloader")}
      initialSettings={toolBehaviorSettings(snapshot, "directdownloader")}
    />
  ),
  webvideodownloader: (snapshot) => <WebVideoDownloaderTool initialSettings={downloaderSettings(snapshot, "webvideodownloader")} />,
  tgdownloader: (snapshot) => <TgDownloaderTool initialSettings={downloaderSettings(snapshot, "tgdownloader")} />,
  zipandpng: (snapshot) => <ZipPngTool initialOutputDir={toolOutputDir(snapshot, "zipandpng")} />,
};

export const pluginPanelRenderers: Record<string, PanelRenderer> = {
  "plugin:json_tools": () => <JsonToolsPluginTool />,
  "plugin:regex_tools": () => <RegexToolsPluginTool />,
  "plugin:csv_tools": () => <CsvToolsPluginTool />,
  "plugin:file_hasher": () => <FileHasherPluginTool />,
  "plugin:archive_extractor": (snapshot) => <ArchiveExtractorPluginTool initialSettings={snapshot?.tool_settings?.archive_extractor ?? {}} />,
  "plugin:text_tools": () => <TextToolsPluginTool />,
  "plugin:timestamp_tools": () => <TimestampToolsPluginTool />,
  "plugin:url_tools": () => <UrlToolsPluginTool />,
  "plugin:uuid_tools": () => <UuidToolsPluginTool />,
};
