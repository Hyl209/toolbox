# Round 2: Remaining Fixes

## Fix 1: test_download_url_with_ytdlp_uses_aria2_and_stability_options 测试污染 (CRITICAL)

**文件:** `modules/video-downloader/tests_video_downloader.py`
**行号:** ~840 (assert line)

**根因:** `captured_opts` 有 6 个条目而不是 2 个。前一个测试 `test_download_web_task_falls_back_to_page_media_candidates_when_ytdlp_rejects_page_url` 调用 `_download_web_task()`，该函数内部调用 `_extract_ytdlp_entry_candidates()`，后者也使用 `from yt_dlp import YoutubeDL`。aria2 测试把 `sys.modules['yt_dlp']` 替换为 FakeYoutubeDL，所以 polluter 测试遗留的 `_extract_ytdlp_entry_candidates` 调用也被捕获到 `captured_opts` 中。最终 `captured_opts[-1]` 是一个额外的 probe opts（没有 `external_downloader`）。

**修复:** 不要用 `captured_opts[-1]`，改为找到包含 download opts 的条目：

```python
# 找到包含 external_downloader 的 opts（即 download opts，不是 probe opts）
download_opts = next(o for o in captured_opts if 'external_downloader' in o)
```

同时删除之前加的 debug prints（`_sh_fresh` 那段防御性代码可以保留，它没有坏处）。

**验证命令:** 
```
python -m pytest modules/video-downloader/tests_video_downloader.py -q --tb=short
```
预期：63 passed, 0 failed。

## Fix 2: `_collect_config_from_form` 共享引用

**文件:** `modules/word-formatter/tab.py`
**方法:** `_collect_config_from_form`
**行:** `config['styles'] = self.config['styles']`
**修复:** 改为 `config['styles'] = dict(self.config['styles'])`

## Fix 3: `run_download` 多余 hasattr

**文件:** `modules/video-downloader/tab.py`
**行:** 907
**修复:** `if hasattr(self, 'cleanup_worker'):` → `self.cleanup_worker()`

## 执行要求

1. 先修 Fix 1（测试），跑 `python -m pytest modules/video-downloader/tests_video_downloader.py -q --tb=short` 确认全部通过
2. 再修 Fix 2 和 Fix 3
3. 跑全量测试确认无回归
4. git commit
5. 用 `python` 不要用 `python3`
