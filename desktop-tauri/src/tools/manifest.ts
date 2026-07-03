export type ToolManifestItem = {
  id: string;
  title: string;
  category: string;
  supported_in_tauri: boolean;
  status: 'ready' | 'pending' | 'planned';
  sidebar_label?: string;
  dir_name?: string;
  converter_file?: string;
  tab_file?: string;
  extra_files?: readonly string[];
  tab_kwargs?: Record<string, unknown>;
};

export const toolManifest = [
  {
    "id": "aiimage",
    "title": "AI生图",
    "category": "image",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "AI 生图",
    "dir_name": "modules/ai-image-gen",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "music",
    "title": "NCM转换",
    "category": "audio",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "NCM 转 MP3",
    "dir_name": "modules/ncm-converter",
    "converter_file": "ncm_to_mp3.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "zipandpng",
    "title": "PNG伪装",
    "category": "image",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "图片伪装",
    "dir_name": "modules/file-disguise",
    "converter_file": "zipandpng.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "mp4mp3",
    "title": "MP4转MP3",
    "category": "audio",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "MP4 转 MP3",
    "dir_name": "modules/audio-extractor",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [
      "config_store.py"
    ],
    "tab_kwargs": {}
  },
  {
    "id": "imageconvert",
    "title": "图片格式互转",
    "category": "image",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "图片格式互转",
    "dir_name": "modules/image-converter",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "pdftools",
    "title": "PDF工具",
    "category": "document",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "PDF工具",
    "dir_name": "modules/pdf-tools",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "tgdownloader",
    "title": "TG下载",
    "category": "download",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "TG下载",
    "dir_name": "modules/video-downloader",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [
      "bin/aria2c.exe",
      "bin/aria2c.SHA256.txt"
    ],
    "tab_kwargs": {
      "source_mode": "telegram"
    }
  },
  {
    "id": "webvideodownloader",
    "title": "网页视频下载",
    "category": "download",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "网页视频下载",
    "dir_name": "modules/video-downloader",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {
      "source_mode": "web"
    }
  },
  {
    "id": "directdownloader",
    "title": "直链下载",
    "category": "download",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "直链下载",
    "dir_name": "modules/direct-downloader",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "batchrename",
    "title": "批量命名",
    "category": "file",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "批量命名",
    "dir_name": "modules/batch-rename",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "filesorter",
    "title": "文件分类",
    "category": "file",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "文件分类",
    "dir_name": "modules/file-sorter",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "same",
    "title": "重复文件",
    "category": "file",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "重复文件",
    "dir_name": "modules/duplicate-finder",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "base64",
    "title": "文件Base64",
    "category": "text",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "文件Base64",
    "dir_name": "modules/base64",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  },
  {
    "id": "wordformatter",
    "title": "Word排版统一",
    "category": "text",
    "supported_in_tauri": true,
    "status": "ready",
    "sidebar_label": "Word排版",
    "dir_name": "modules/word-formatter",
    "converter_file": "converter.py",
    "tab_file": "tab.py",
    "extra_files": [],
    "tab_kwargs": {}
  }
] as const satisfies readonly ToolManifestItem[];

export default toolManifest;
