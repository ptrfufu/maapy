"""DLL 加载模块——平台感知。
验证: tests/min.py 已确认 os.chdir + ffi.dlopen 方案在 Windows 上可行。
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from ._ffi import ffi


_LOAD_LOCK = threading.Lock()
_DLL_DIR_HANDLES: list[object] = []


def load_lib(core_dir: str | Path):
    """加载 MaaCore DLL/SO 并返回 lib 对象。

    Args:
        core_dir: MaaCore.dll 所在目录（也包含 resource 子目录）

    Returns:
        CFFI lib 对象

    Raises:
        OSError: DLL 加载失败
    """
    core_dir = Path(core_dir).resolve()
    if not core_dir.is_dir():
        raise OSError(f"目录不存在: {core_dir}")

    with _LOAD_LOCK:
        _init_platform_path(str(core_dir))

        lib_name = _lib_name()
        lib_path = core_dir / lib_name
        if not lib_path.is_file():
            raise OSError(f"找不到 {lib_name}: {lib_path}")

        original_cwd = os.getcwd()
        try:
            os.chdir(str(core_dir))
            lib = ffi.dlopen(str(lib_path))
        finally:
            os.chdir(original_cwd)
        return lib


def _lib_name() -> str:
    """返回当前平台的库文件名。"""
    if sys.platform == "win32":
        return "MaaCore.dll"
    elif sys.platform == "darwin":
        return "libMaaCore.dylib"
    else:
        return "libMaaCore.so"


def _init_platform_path(core_dir: str) -> None:
    """将 core_dir 加入动态链接搜索路径。"""
    if sys.platform == "win32":
        try:
            _DLL_DIR_HANDLES.append(os.add_dll_directory(core_dir))
        except AttributeError:
            # Python < 3.8
            os.environ["PATH"] = core_dir + os.pathsep + os.environ.get("PATH", "")
    elif sys.platform == "darwin":
        os.environ["DYLD_LIBRARY_PATH"] = (
            core_dir + os.pathsep + os.environ.get("DYLD_LIBRARY_PATH", "")
        )
    else:
        os.environ["LD_LIBRARY_PATH"] = (
            core_dir + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
        )
