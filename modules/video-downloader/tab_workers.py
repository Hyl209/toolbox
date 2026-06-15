from __future__ import annotations

from pathlib import Path


def build_worker_classes(QObject, QThread, Signal, _FallbackSignal):
    if QObject is not None and Signal is not None:
        class DownloadWorker(QObject):
            progress = Signal(str)
            finished = Signal(list)
            failed = Signal(str)
            cancelled = Signal()

            def __init__(self, module, tasks, output_dir, telegram_config, options, token=None):
                super().__init__()
                self.module = module
                self.tasks = tasks
                self.output_dir = output_dir
                self.telegram_config = telegram_config
                self.options = options
                self._token = token

            def run(self):
                try:
                    results = self.module.download_batch(
                        self.tasks,
                        self.output_dir,
                        self.telegram_config,
                        self.options,
                        progress_cb=self.progress.emit,
                        token=self._token,
                    )
                    self.finished.emit(results)
                except self.module.CancelledError:
                    self.cancelled.emit()
                except Exception as exc:
                    self.failed.emit(str(exc))

        class ScanWorker(QObject):
            progress = Signal(str)
            finished = Signal(list)
            failed = Signal(str)

            def __init__(self, module, urls, options=None):
                super().__init__()
                self.module = module
                self.urls = urls
                self.options = options

            def run(self):
                try:
                    results = self.module.inspect_web_media_batch(self.urls, progress_cb=self.progress.emit, options=self.options)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

        class ThumbnailWorker(QObject):
            progress = Signal(str)
            finished = Signal(list)
            failed = Signal(str)

            def __init__(self, module, files, source_url, candidate_index=None, thumbnail_mode='web_then_frame', proxy_url=''):
                super().__init__()
                self.module = module
                self.files = files
                self.source_url = source_url
                self.candidate_index = candidate_index
                self.thumbnail_mode = thumbnail_mode
                self.proxy_url = proxy_url

            def run(self):
                try:
                    results = []
                    for i, fpath in enumerate(self.files, 1):
                        self.progress.emit(f'补封面 {i}/{len(self.files)}: {Path(fpath).name}')
                        result = self.module.embed_thumbnail(
                            fpath, self.source_url,
                            progress_cb=self.progress.emit,
                            candidate_index=self.candidate_index,
                            thumbnail_mode=self.thumbnail_mode,
                            proxy_url=self.proxy_url,
                        )
                        result['_index'] = i
                        result['_path'] = str(fpath)
                        results.append(result)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))
    else:
        class DownloadWorker:
            def __init__(self, module, tasks, output_dir, telegram_config, options, token=None):
                self.module = module
                self.tasks = tasks
                self.output_dir = output_dir
                self.telegram_config = telegram_config
                self.options = options
                self._token = token
                self.progress = _FallbackSignal()
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()
                self.cancelled = _FallbackSignal()

            def run(self):
                try:
                    results = self.module.download_batch(
                        self.tasks,
                        self.output_dir,
                        self.telegram_config,
                        self.options,
                        progress_cb=self.progress.emit,
                        token=self._token,
                    )
                    self.finished.emit(results)
                except self.module.CancelledError:
                    self.cancelled.emit()
                except Exception as exc:
                    self.failed.emit(str(exc))

        class ScanWorker:
            def __init__(self, module, urls, options=None):
                self.module = module
                self.urls = urls
                self.options = options
                self.progress = _FallbackSignal()
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()

            def run(self):
                try:
                    results = self.module.inspect_web_media_batch(self.urls, progress_cb=self.progress.emit, options=self.options)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

        class ThumbnailWorker:
            def __init__(self, module, files, source_url, candidate_index=None, thumbnail_mode='web_then_frame', proxy_url=''):
                self.module = module
                self.files = files
                self.source_url = source_url
                self.candidate_index = candidate_index
                self.thumbnail_mode = thumbnail_mode
                self.proxy_url = proxy_url
                self.progress = _FallbackSignal()
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()

            def run(self):
                try:
                    results = []
                    for i, fpath in enumerate(self.files, 1):
                        self.progress.emit(f'补封面 {i}/{len(self.files)}: {Path(fpath).name}')
                        result = self.module.embed_thumbnail(
                            fpath, self.source_url,
                            progress_cb=self.progress.emit,
                            candidate_index=self.candidate_index,
                            thumbnail_mode=self.thumbnail_mode,
                            proxy_url=self.proxy_url,
                        )
                        result['_index'] = i
                        result['_path'] = str(fpath)
                        results.append(result)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

    return DownloadWorker, ScanWorker, ThumbnailWorker
