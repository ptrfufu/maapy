"""C 函数的薄封装层。
处理 str↔bytes 编码、缓冲区分配、AsstBool 返回值检查。
"""

from __future__ import annotations

import json
from typing import Any

from ._ffi import ffi


# ── 工具函数 ──

def _encode(s: str) -> bytes:
    """字符串 → UTF-8 bytes，供 C 函数使用。"""
    return s.encode("utf-8")


def _decode(b: bytes | None) -> str:
    """C 返回的 bytes → Python str。"""
    if b is None:
        return ""
    return b.decode("utf-8")


def _encode_json(obj: dict[str, Any]) -> bytes:
    """Python dict → JSON bytes。"""
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


# ── 全局函数 ──

def asst_set_user_dir(lib, path: str) -> bool:
    return lib.AsstSetUserDir(_encode(path)) != 0


def asst_load_resource(lib, path: str) -> bool:
    return lib.AsstLoadResource(_encode(path)) != 0


def asst_set_static_option(lib, key: int, value: str) -> bool:
    return lib.AsstSetStaticOption(key, _encode(value)) != 0


# ── 实例生命周期 ──

def asst_create_ex(lib, callback, custom_arg=ffi.NULL):
    return lib.AsstCreateEx(callback, custom_arg)


def asst_destroy(lib, handle) -> None:
    lib.AsstDestroy(handle)


# ── 实例选项 ──

def asst_set_instance_option(lib, handle, key: int, value: str) -> bool:
    return lib.AsstSetInstanceOption(handle, key, _encode(value)) != 0


# ── 连接 ──

def asst_async_connect(lib, handle, adb_path: str, address: str, config: str = "General", block: bool = False) -> int:
    return lib.AsstAsyncConnect(handle, _encode(adb_path), _encode(address), _encode(config), 1 if block else 0)


def asst_set_connection_extras(lib, name: str, extras: dict[str, Any]) -> None:
    lib.AsstSetConnectionExtras(_encode(name), _encode_json(extras))


def asst_connected(lib, handle) -> bool:
    return lib.AsstConnected(handle) != 0


# ── 任务管理 ──

def asst_append_task(lib, handle, type_name: str, params: dict[str, Any]) -> int:
    return lib.AsstAppendTask(handle, _encode(type_name), _encode_json(params))


def asst_set_task_params(lib, handle, task_id: int, params: dict[str, Any]) -> bool:
    return lib.AsstSetTaskParams(handle, task_id, _encode_json(params)) != 0


def asst_start(lib, handle) -> bool:
    return lib.AsstStart(handle) != 0


def asst_stop(lib, handle) -> bool:
    return lib.AsstStop(handle) != 0


def asst_running(lib, handle) -> bool:
    return lib.AsstRunning(handle) != 0


def asst_back_to_home(lib, handle) -> bool:
    return lib.AsstBackToHome(handle) != 0


# ── 异步操作 ──

def asst_async_click(lib, handle, x: int, y: int, block: bool = False) -> int:
    return lib.AsstAsyncClick(handle, x, y, 1 if block else 0)


def asst_async_screencap(lib, handle, block: bool = False) -> int:
    return lib.AsstAsyncScreencap(handle, 1 if block else 0)


# ── 数据获取 ──

def asst_get_image(lib, handle) -> bytes | None:
    """获取上次截图的 RGBA 数据。"""
    null_size = asst_get_null_size(lib)
    size = lib.AsstGetImage(handle, ffi.NULL, 0)
    if size == null_size:
        return None

    buf = ffi.new("unsigned char[]", size)
    actual = lib.AsstGetImage(handle, buf, size)
    if actual == null_size:
        return None

    return bytes(ffi.buffer(buf, actual))


def asst_get_image_bgr(lib, handle) -> bytes | None:
    """获取上次截图的 BGR 数据（OpenCV 格式）。"""
    null_size = asst_get_null_size(lib)
    size = lib.AsstGetImageBgr(handle, ffi.NULL, 0)
    if size == null_size:
        return None

    buf = ffi.new("unsigned char[]", size)
    actual = lib.AsstGetImageBgr(handle, buf, size)
    if actual == null_size:
        return None

    return bytes(ffi.buffer(buf, actual))


def asst_get_uuid(lib, handle) -> str:
    buf = ffi.new("char[]", 256)
    size = lib.AsstGetUUID(handle, buf, 256)
    null_size = asst_get_null_size(lib)
    if size == null_size:
        return ""
    raw: bytes = ffi.string(buf)  # type: ignore[assignment]
    return _decode(raw)


def asst_get_tasks_list(lib, handle) -> list[int]:
    buf = ffi.new("int32_t[]", 64)
    count = lib.AsstGetTasksList(handle, buf, 64)
    return [buf[i] for i in range(count)]


def asst_get_null_size(lib) -> int:
    return lib.AsstGetNullSize()


# ── 其他 ──

def asst_get_version(lib) -> str:
    return _decode(ffi.string(lib.AsstGetVersion()))


def asst_log(lib, level: str, message: str) -> None:
    lib.AsstLog(_encode(level), _encode(message))
