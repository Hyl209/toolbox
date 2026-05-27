from __future__ import annotations


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

            def __init__(self, module, urls):
                super().__init__()
                self.module = module
                self.urls = urls

            def run(self):
                try:
                    results = self.module.inspect_web_media_batch(self.urls, progress_cb=self.progress.emit)
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
            def __init__(self, module, urls):
                self.module = module
                self.urls = urls
                self.progress = _FallbackSignal()
                self.finished = _FallbackSignal()
                self.failed = _FallbackSignal()

            def run(self):
                try:
                    results = self.module.inspect_web_media_batch(self.urls, progress_cb=self.progress.emit)
                    self.finished.emit(results)
                except Exception as exc:
                    self.failed.emit(str(exc))

    return DownloadWorker, ScanWorker
