"""CFFI 类型声明与 ffi 实例。
来源: AsstCaller.h (MaaAssistantArknights/include/AsstCaller.h)
"""

from __future__ import annotations

import sys

import cffi

ffi = cffi.FFI()

# ── 回调类型声明（Windows 用 __stdcall，Linux/macOS 用 cdecl） ──
if sys.platform == "win32":
    CALL = "__stdcall "
    CALLBACK_DECL = "typedef void (__stdcall *AsstApiCallback)(AsstMsgId, const char*, void*);"
else:
    CALL = ""
    CALLBACK_DECL = "typedef void (*AsstApiCallback)(AsstMsgId, const char*, void*);"

if sys.platform == "win32":
    WIN32_DECL = """
    typedef enum AsstWin32ScreencapMethodEnum
    {
        AsstWin32ScreencapMethod_None = 0,
        AsstWin32ScreencapMethod_GDI = 1,
        AsstWin32ScreencapMethod_FramePool = 1 << 1,
        AsstWin32ScreencapMethod_DXGI_DesktopDup = 1 << 2,
        AsstWin32ScreencapMethod_DXGI_DesktopDup_Window = 1 << 3,
        AsstWin32ScreencapMethod_PrintWindow = 1 << 4,
        AsstWin32ScreencapMethod_ScreenDC = 1 << 5,
    } AsstWin32ScreencapMethodEnum;

    typedef enum AsstWin32InputMethodEnum
    {
        AsstWin32InputMethod_None = 0,
        AsstWin32InputMethod_Seize = 1,
        AsstWin32InputMethod_SendMessage = 1 << 1,
        AsstWin32InputMethod_PostMessage = 1 << 2,
        AsstWin32InputMethod_LegacyEvent = 1 << 3,
        AsstWin32InputMethod_PostThreadMessage = 1 << 4,
        AsstWin32InputMethod_SendMessageWithCursorPos = 1 << 5,
        AsstWin32InputMethod_PostMessageWithCursorPos = 1 << 6,
        AsstWin32InputMethod_SendMessageWithWindowPos = 1 << 7,
        AsstWin32InputMethod_PostMessageWithWindowPos = 1 << 8,
    } AsstWin32InputMethodEnum;
"""
else:
    WIN32_DECL = ""

ffi.cdef(
    """
    struct AsstExtAPI;
    typedef struct AsstExtAPI* AsstHandle;

    typedef uint8_t  AsstBool;
    typedef uint64_t AsstSize;
    typedef int32_t  AsstId;
    typedef AsstId   AsstMsgId;
    typedef AsstId   AsstTaskId;
    typedef AsstId   AsstAsyncCallId;
    typedef int32_t  AsstOptionKey;
    typedef AsstOptionKey AsstStaticOptionKey;
    typedef AsstOptionKey AsstInstanceOptionKey;

"""
    + WIN32_DECL
    + CALLBACK_DECL
    + f"""
    // ── 全局函数 ──
    AsstBool {CALL}AsstSetUserDir(const char* path);
    AsstBool {CALL}AsstLoadResource(const char* path);
    AsstBool {CALL}AsstSetStaticOption(AsstStaticOptionKey key, const char* value);

    // ── 实例生命周期 ──
    AsstHandle {CALL}AsstCreate(void);
    AsstHandle {CALL}AsstCreateEx(AsstApiCallback callback, void* custom_arg);
    void {CALL}AsstDestroy(AsstHandle handle);

    // ── 实例选项 ──
    AsstBool {CALL}AsstSetInstanceOption(AsstHandle handle, AsstInstanceOptionKey key, const char* value);

    // ── 连接 ──
    AsstBool {CALL}AsstConnect(AsstHandle handle, const char* adb_path, const char* address, const char* config);
    AsstAsyncCallId {CALL}AsstAsyncConnect(AsstHandle handle, const char* adb_path, const char* address, const char* config, AsstBool block);
    void {CALL}AsstSetConnectionExtras(const char* name, const char* extras);
    AsstBool {CALL}AsstConnected(AsstHandle handle);

    AsstBool {CALL}AsstAttachWindow(
        AsstHandle handle,
        void* hwnd,
        uint64_t screencap_method,
        uint64_t mouse_method,
        uint64_t keyboard_method);
    AsstAsyncCallId {CALL}AsstAsyncAttachWindow(
        AsstHandle handle,
        void* hwnd,
        uint64_t screencap_method,
        uint64_t mouse_method,
        uint64_t keyboard_method,
        AsstBool block);

    // ── 任务管理 ──
    AsstTaskId {CALL}AsstAppendTask(AsstHandle handle, const char* type, const char* params);
    AsstBool {CALL}AsstSetTaskParams(AsstHandle handle, AsstTaskId id, const char* params);
    AsstBool {CALL}AsstStart(AsstHandle handle);
    AsstBool {CALL}AsstStop(AsstHandle handle);
    AsstBool {CALL}AsstRunning(AsstHandle handle);
    AsstBool {CALL}AsstBackToHome(AsstHandle handle);

    // ── 异步操作 ──
    AsstAsyncCallId {CALL}AsstAsyncClick(AsstHandle handle, int32_t x, int32_t y, AsstBool block);
    AsstAsyncCallId {CALL}AsstAsyncScreencap(AsstHandle handle, AsstBool block);

    // ── 数据获取 ──
    AsstSize {CALL}AsstGetImage(AsstHandle handle, void* buff, AsstSize buff_size);
    AsstSize {CALL}AsstGetImageBgr(AsstHandle handle, void* buff, AsstSize buff_size);
    AsstSize {CALL}AsstGetUUID(AsstHandle handle, char* buff, AsstSize buff_size);
    AsstSize {CALL}AsstGetTasksList(AsstHandle handle, AsstTaskId* buff, AsstSize buff_size);
    AsstSize {CALL}AsstGetNullSize(void);

    // ── 其他 ──
    const char* {CALL}AsstGetVersion(void);
    void {CALL}AsstLog(const char* level, const char* message);
"""
)

# 导出回调类型名供 ffi.callback(...) 使用
ASST_API_CALLBACK_TYPE = "AsstApiCallback"
