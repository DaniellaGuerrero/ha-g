from __future__ import annotations

from typing import Any, Callable, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from api_client import ApiError


class ApiWorker(QThread):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, func: Callable[..., Any], *args: Any) -> None:
        super().__init__()
        self._func = func
        self._args = args

    def run(self) -> None:
        try:
            result = self._func(*self._args)
        except ApiError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Unexpected error: {exc}")
        else:
            self.succeeded.emit(result)


_active: set[ApiWorker] = set()


def run_in_background(
    func: Callable[..., Any],
    *args: Any,
    on_success: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> ApiWorker:
    worker = ApiWorker(func, *args)
    _active.add(worker)
    if on_success:
        worker.succeeded.connect(on_success)
    if on_error:
        worker.failed.connect(on_error)
    worker.finished.connect(lambda w=worker: _active.discard(w))
    worker.start()
    return worker


def wait_for_workers(timeout_ms: int = 3000) -> None:
    for worker in list(_active):
        worker.wait(timeout_ms)
