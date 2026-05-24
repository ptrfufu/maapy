"""CFFI 类型声明与 ffi 实例。
来源: AsstCaller.h (MaaAssistantArknights/include/AsstCaller.h)
"""

from __future__ import annotations

import sys

import cffi

ffi = cffi.FFI()

# ── 回调类型声明（Windows 用 __stdcall，Linux/macOS 用 cdecl） ──
if sys.platform == "win32":
    CALLBACK_DECL = "typedef void __stdcall AsstApiCallback(int32_t, const char*, void*);"
else:
    CALLBACK_DECL = "typedef void AsstApiCallback(int32_t, const char*, void*);"

ffi.cdef(
    """
    typedef uint8_t  AsstBool;
    typedef uint64_t AsstSize;
    typedef int32_t  AsstMsgId;
    typedef int32_t  AsstTaskId;
    typedef int32_t  AsstAsyncCallId;
    typedef int32_t  AsstOptionKey;

"""
    + CALLBACK_DECL
    + """
    // ── 全局函数 ──
    AsstBool AsstSetUserDir(const char* path);
    AsstBool AsstLoadResource(const char* path);
    AsstBool AsstSetStaticOption(AsstOptionKey key, const char* value);

    // ── 实例生命周期 ──
    void* AsstCreate(void);
    void* AsstCreateEx(AsstApiCallback* callback, void* custom_arg);
    void  AsstDestroy(void* handle);

    // ── 实例选项 ──
    AsstBool AsstSetInstanceOption(void* handle, AsstOptionKey key, const char* value);

    // ── 连接 ──
    AsstBool AsstConnect(void* handle, const char* adb_path, const char* address, const char* config);
    AsstAsyncCallId AsstAsyncConnect(void* handle, const char* adb_path, const char* address, const char* config, AsstBool block);
    void AsstSetConnectionExtras(const char* name, const char* extras);
    AsstBool AsstConnected(void* handle);

    // ── 任务管理 ──
    AsstTaskId AsstAppendTask(void* handle, const char* type, const char* params);
    AsstBool AsstSetTaskParams(void* handle, AsstTaskId id, const char* params);
    AsstBool AsstStart(void* handle);
    AsstBool AsstStop(void* handle);
    AsstBool AsstRunning(void* handle);
    AsstBool AsstBackToHome(void* handle);

    // ── 异步操作 ──
    AsstAsyncCallId AsstAsyncClick(void* handle, int32_t x, int32_t y, AsstBool block);
    AsstAsyncCallId AsstAsyncScreencap(void* handle, AsstBool block);

    // ── 数据获取 ──
    AsstSize AsstGetImage(void* handle, void* buff, AsstSize buff_size);
    AsstSize AsstGetImageBgr(void* handle, void* buff, AsstSize buff_size);
    AsstSize AsstGetUUID(void* handle, char* buff, AsstSize buff_size);
    AsstSize AsstGetTasksList(void* handle, AsstTaskId* buff, AsstSize buff_size);
    AsstSize AsstGetNullSize(void);

    // ── 其他 ──
    const char* AsstGetVersion(void);
    void AsstLog(const char* level, const char* message);
"""
)

# 导出回调类型名供 ffi.callback(...) 使用
ASST_API_CALLBACK_TYPE = "AsstApiCallback"
