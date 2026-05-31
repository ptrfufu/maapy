"""Instance——MaaCore handle 生命周期管理。
一个 Instance = 一个 AsstHandle = 一台设备。
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, cast

from ._ffi import ffi
from .connection import ConnectionExtras
from ._json import JsonDict
from ._loader import load_lib
from ._lowlevel import (
    asst_append_task,
    asst_async_attach_window,
    asst_async_click,
    asst_async_connect,
    asst_async_screencap,
    asst_attach_window,
    asst_back_to_home,
    asst_connected,
    asst_create_ex,
    asst_destroy,
    asst_get_image,
    asst_get_image_bgr,
    asst_get_null_size,
    asst_get_uuid,
    asst_get_version,
    asst_load_resource,
    asst_log,
    asst_running,
    asst_set_connection_extras,
    asst_set_instance_option,
    asst_set_static_option,
    asst_set_task_params,
    asst_set_user_dir,
    asst_start,
    asst_stop,
)
from .callback import CallbackManager
from .exceptions import MaaConnectionError, MaaDataError, MaaLoadError, MaaTaskError


class Instance:
    """MaaCore 实例——封装一个 AsstHandle。

    不应直接构造，请使用 MaaClient。
    """

    def __init__(self, callback_mgr: CallbackManager) -> None:
        self._lib = _get_lib()
        self._callback_mgr = callback_mgr
        self._handle = cast(Any, self._lib).AsstCreateEx(callback_mgr.c_callback, ffi.NULL)
        if self._handle == ffi.NULL:
            raise MaaLoadError("AsstCreateEx 返回空句柄")
        self._closed = False

    @property
    def handle(self):
        return self._require_handle()

    @property
    def callback_mgr(self) -> CallbackManager:
        return self._callback_mgr

    # ── 连接 ──

    def connect(
        self,
        adb_path: str,
        address: str,
        config: str = "General",
        timeout: float = 30.0,
    ) -> bool:
        """异步连接设备，阻塞等待连接成功或超时。"""
        from .events._base import Event
        from .events.global_events import ConnectionEvent

        done = threading.Event()

        def _on_connected(event: Event) -> None:
            if isinstance(event, ConnectionEvent) and event.connected:
                done.set()

        subscription = self._callback_mgr.subscribe(ConnectionEvent, _on_connected)
        try:
            call_id = asst_async_connect(self._lib, self._require_handle(), adb_path, address, config, block=False)
            if call_id == 0:
                raise MaaConnectionError("AsstAsyncConnect 未能发起连接")
            if done.wait(timeout=timeout):
                return True
            if asst_connected(self._lib, self._require_handle()):
                return True
            raise MaaConnectionError(f"连接超时: {address}")
        finally:
            subscription.close()

    @property
    def connected(self) -> bool:
        return asst_connected(self._lib, self._require_handle())

    def attach_window(
        self,
        hwnd: int,
        screencap_method: int,
        mouse_method: int,
        keyboard_method: int,
    ) -> bool:
        return asst_attach_window(
            self._lib,
            self._require_handle(),
            hwnd,
            screencap_method,
            mouse_method,
            keyboard_method,
        )

    def async_attach_window(
        self,
        hwnd: int,
        screencap_method: int,
        mouse_method: int,
        keyboard_method: int,
        *,
        block: bool = False,
    ) -> int:
        return asst_async_attach_window(
            self._lib,
            self._require_handle(),
            hwnd,
            screencap_method,
            mouse_method,
            keyboard_method,
            block=block,
        )

    def set_connection_extras(self, extras: ConnectionExtras) -> None:
        asst_set_connection_extras(self._lib, extras)

    # ── 任务 ──

    def append_task(self, type_name: str, params: JsonDict) -> int:
        task_id = asst_append_task(self._lib, self._require_handle(), type_name, params)
        if task_id == 0:
            raise MaaTaskError(f"添加任务失败: {type_name}")
        return task_id

    def set_task_params(self, task_id: int, params: JsonDict) -> bool:
        return asst_set_task_params(self._lib, self._require_handle(), task_id, params)

    # ── 控制 ──

    def start(self) -> None:
        if not asst_start(self._lib, self._require_handle()):
            raise MaaTaskError("AsstStart 失败")

    def stop(self) -> None:
        if not self._closed and self._handle is not None:
            if not asst_stop(self._lib, self._handle):
                raise MaaTaskError("AsstStop 失败")

    @property
    def running(self) -> bool:
        return asst_running(self._lib, self._require_handle())

    def back_to_home(self) -> bool:
        return asst_back_to_home(self._lib, self._require_handle())

    # ── 异步操作 ──

    def click(self, x: int, y: int) -> int:
        return asst_async_click(self._lib, self._require_handle(), x, y)

    def screencap(self) -> int:
        return asst_async_screencap(self._lib, self._require_handle())

    # ── 数据 ──

    def get_image(self) -> bytes:
        return asst_get_image(self._lib, self._require_handle())

    def get_image_bgr(self) -> bytes:
        return asst_get_image_bgr(self._lib, self._require_handle())

    def get_uuid(self) -> str:
        return asst_get_uuid(self._lib, self._require_handle())

    @property
    def uuid(self) -> str:
        return self.get_uuid()

    # ── 选项 ──

    def set_instance_option(self, key: int, value: str) -> bool:
        return asst_set_instance_option(self._lib, self._require_handle(), key, value)

    # ── 清理 ──

    def destroy(self) -> None:
        if self._closed:
            return
        if self._handle is not None:
            asst_destroy(self._lib, self._handle)
            self._handle = None
        self._closed = True
        self._callback_mgr.close()

    def _require_handle(self):
        if self._closed or self._handle is None:
            raise MaaLoadError("MaaCore 实例已销毁")
        return self._handle


# ── 模块级单例 — DLL 加载后缓存在此 ──

_lib = None
_loaded = False
_core_dir: Path | None = None
_load_lock = threading.Lock()


def _get_lib():
    global _lib, _loaded
    if _lib is None or not _loaded:
        raise MaaLoadError("MaaCore 未加载，请先调用 MaaClient.load()")
    return _lib


def load_and_init(core_dir: str | Path, user_dir: str | None = None) -> str:
    """加载 DLL 并初始化全局资源。返回版本号。"""
    global _lib, _loaded, _core_dir
    with _load_lock:
        if _loaded:
            raise MaaLoadError("MaaCore 已加载，不可重复加载")

        core_dir = Path(core_dir).resolve()
        lib = load_lib(core_dir)
        version = asst_get_version(lib)

        target_user_dir = str(user_dir or core_dir / "user")
        Path(target_user_dir).mkdir(parents=True, exist_ok=True)
        if not asst_set_user_dir(lib, target_user_dir):
            raise MaaLoadError(f"AsstSetUserDir 失败: {target_user_dir}")

        if not asst_load_resource(lib, str(core_dir)):
            raise MaaLoadError(f"AsstLoadResource 失败: {core_dir}")

        _lib = lib
        _loaded = True
        _core_dir = core_dir
        return version


def set_static_option(key: int, value: str) -> bool:
    return asst_set_static_option(_get_lib(), key, value)


def get_version() -> str | None:
    try:
        lib = _get_lib()
    except MaaLoadError:
        return None
    v = asst_get_version(lib)
    return v


def get_core_dir() -> Path | None:
    return _core_dir if _loaded else None


def log(level: str, message: str) -> None:
    asst_log(_get_lib(), level, message)
