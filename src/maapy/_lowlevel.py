"""C 函数的薄封装层。
处理 str↔bytes 编码、缓冲区分配、AsstBool 返回值检查。
"""

from __future__ import annotations

from typing import Any, cast

from ._ffi import ffi
from .connection import ConnectionExtras
from ._json import JsonDict, encode_json
from .exceptions import MaaDataError


_DEFAULT_IMAGE_BUFFER_SIZE = 1280 * 720 * 3
_MAX_IMAGE_BUFFER_SIZE = 10 * 1920 * 1080 * 4


# ── 工具函数 ──

def _encode(s: str) -> bytes:
    """字符串 → UTF-8 bytes，供 C 函数使用。"""
    return s.encode("utf-8")


def _decode(b: bytes | None) -> str:
    """C 返回的 bytes → Python str。"""
    if b is None:
        return ""
    return b.decode("utf-8")


def _ffi_string(value: Any) -> bytes | None:
    if value == ffi.NULL:
        return None
    return cast(bytes, ffi.string(value))


def _encode_json(obj: JsonDict) -> bytes:
    """Python dict → JSON bytes。"""
    return encode_json(obj)


def _read_sized_buffer(lib: Any, reader: Any, handle: Any, initial_size: int) -> bytes:
    null_size = asst_get_null_size(lib)
    size = initial_size

    while size <= _MAX_IMAGE_BUFFER_SIZE:
        buf = ffi.new("unsigned char[]", size)
        actual = reader(handle, buf, size)
        if actual != null_size:
            return bytes(ffi.buffer(buf, actual))
        size *= 2

    raise MaaDataError(f"截图数据超过最大缓冲区: {_MAX_IMAGE_BUFFER_SIZE}")


# ── 全局函数 ──

def asst_set_user_dir(lib: Any, path: str) -> bool:
    return lib.AsstSetUserDir(_encode(path)) != 0


def asst_load_resource(lib: Any, path: str) -> bool:
    return lib.AsstLoadResource(_encode(path)) != 0


def asst_set_static_option(lib: Any, key: int, value: str) -> bool:
    return lib.AsstSetStaticOption(key, _encode(value)) != 0


# ── 实例生命周期 ──

def asst_create(lib: Any) -> Any:
    return lib.AsstCreate()


def asst_create_ex(lib: Any, callback: Any, custom_arg: Any = ffi.NULL) -> Any:
    return lib.AsstCreateEx(callback, custom_arg)


def asst_destroy(lib: Any, handle: Any) -> None:
    lib.AsstDestroy(handle)


# ── 实例选项 ──

def asst_set_instance_option(lib: Any, handle: Any, key: int, value: str) -> bool:
    return lib.AsstSetInstanceOption(handle, key, _encode(value)) != 0


# ── 连接 ──

def asst_connect(lib: Any, handle: Any, adb_path: str, address: str, config: str = "General") -> bool:
    return lib.AsstConnect(handle, _encode(adb_path), _encode(address), _encode(config)) != 0


def asst_async_connect(
    lib: Any,
    handle: Any,
    adb_path: str,
    address: str,
    config: str = "General",
    block: bool = False,
) -> int:
    return lib.AsstAsyncConnect(handle, _encode(adb_path), _encode(address), _encode(config), 1 if block else 0)


def asst_set_connection_extras(lib: Any, extras: ConnectionExtras) -> None:
    lib.AsstSetConnectionExtras(_encode(extras.config_name), _encode_json(extras.to_json()))


def asst_connected(lib: Any, handle: Any) -> bool:
    return lib.AsstConnected(handle) != 0


def asst_attach_window(
    lib: Any,
    handle: Any,
    hwnd: int,
    screencap_method: int,
    mouse_method: int,
    keyboard_method: int,
) -> bool:
    return (
        lib.AsstAttachWindow(
            handle,
            ffi.cast("void*", hwnd),
            screencap_method,
            mouse_method,
            keyboard_method,
        )
        != 0
    )


def asst_async_attach_window(
    lib: Any,
    handle: Any,
    hwnd: int,
    screencap_method: int,
    mouse_method: int,
    keyboard_method: int,
    block: bool = False,
) -> int:
    return lib.AsstAsyncAttachWindow(
        handle,
        ffi.cast("void*", hwnd),
        screencap_method,
        mouse_method,
        keyboard_method,
        1 if block else 0,
    )


# ── 任务管理 ──

def asst_append_task(lib: Any, handle: Any, type_name: str, params: JsonDict) -> int:
    return lib.AsstAppendTask(handle, _encode(type_name), _encode_json(params))


def asst_set_task_params(lib: Any, handle: Any, task_id: int, params: JsonDict) -> bool:
    return lib.AsstSetTaskParams(handle, task_id, _encode_json(params)) != 0


def asst_start(lib: Any, handle: Any) -> bool:
    return lib.AsstStart(handle) != 0


def asst_stop(lib: Any, handle: Any) -> bool:
    return lib.AsstStop(handle) != 0


def asst_running(lib: Any, handle: Any) -> bool:
    return lib.AsstRunning(handle) != 0


def asst_back_to_home(lib: Any, handle: Any) -> bool:
    return lib.AsstBackToHome(handle) != 0


# ── 异步操作 ──

def asst_async_click(lib: Any, handle: Any, x: int, y: int, block: bool = False) -> int:
    return lib.AsstAsyncClick(handle, x, y, 1 if block else 0)


def asst_async_screencap(lib: Any, handle: Any, block: bool = False) -> int:
    return lib.AsstAsyncScreencap(handle, 1 if block else 0)


# ── 数据获取 ──

def asst_get_image(lib: Any, handle: Any) -> bytes:
    """获取上次截图的 PNG 数据。"""
    return _read_sized_buffer(lib, lib.AsstGetImage, handle, _DEFAULT_IMAGE_BUFFER_SIZE)


def asst_get_image_bgr(lib: Any, handle: Any) -> bytes:
    """获取上次截图的 BGR 数据（OpenCV 格式）。"""
    return _read_sized_buffer(lib, lib.AsstGetImageBgr, handle, _DEFAULT_IMAGE_BUFFER_SIZE)


def asst_get_uuid(lib: Any, handle: Any) -> str:
    buf = ffi.new("char[]", 256)
    size = lib.AsstGetUUID(handle, buf, 256)
    null_size = asst_get_null_size(lib)
    if size == null_size:
        return ""
    return _decode(_ffi_string(buf))


def asst_get_tasks_list(lib: Any, handle: Any) -> list[int]:
    capacity = 64
    null_size = asst_get_null_size(lib)
    while capacity <= 1024:
        buf = ffi.new("int32_t[]", capacity)
        count = lib.AsstGetTasksList(handle, buf, capacity)
        if count == null_size:
            raise MaaDataError("AsstGetTasksList 返回空值")
        if count <= capacity:
            return [buf[i] for i in range(count)]
        capacity *= 2
    raise MaaDataError(f"AsstGetTasksList 返回数量超过最大缓冲区: {capacity}")


def asst_get_null_size(lib: Any) -> int:
    return lib.AsstGetNullSize()


# ── 其他 ──

def asst_get_version(lib: Any) -> str:
    return _decode(_ffi_string(lib.AsstGetVersion()))


def asst_log(lib: Any, level: str, message: str) -> None:
    lib.AsstLog(_encode(level), _encode(message))
