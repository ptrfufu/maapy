"""自定义异常层次。"""

from __future__ import annotations


class MaaError(Exception):
    """所有 maapy 异常的基类。"""
    pass


class MaaLoadError(MaaError):
    """DLL 加载或初始化失败。"""
    pass


class MaaConnectionError(MaaError):
    """设备连接超时或失败。"""
    pass


class MaaTaskError(MaaError):
    """任务添加或执行失败。"""
    pass


class MaaValidationError(MaaError, ValueError):
    """Python 侧参数校验失败。"""
    pass


class MaaDataError(MaaError):
    """数据获取失败（截图、UUID 等）。"""
    pass


class MaaCallbackError(MaaError):
    """回调内部异常（不会向 C 栈抛出）。"""
    pass
