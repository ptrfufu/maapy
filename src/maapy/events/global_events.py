"""全局消息事件 (msg 0-5)。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import Event


@dataclass(slots=True, frozen=True)
class InternalErrorEvent(Event):
    """msg=0: 内部错误。"""
    pass


@dataclass(slots=True, frozen=True)
class InitFailedEvent(Event):
    """msg=1: 初始化失败。"""
    what: str = ""
    why: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ConnectionEvent(Event):
    """msg=2: 连接状态变更。"""
    what: str = ""
    why: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    connected: bool = False  # what="Connected" 或 "UuidGot" 时为 True


@dataclass(slots=True, frozen=True)
class AllTasksCompletedEvent(Event):
    """msg=3: 任务队列全部完成。"""
    taskchain: str = ""
    finished_tasks: list[int] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class AsyncCallInfoEvent(Event):
    """msg=4: 异步调用完成。"""
    what: str = ""
    async_call_id: int = 0
    ret: bool = False
    cost: int = 0  # 毫秒


@dataclass(slots=True, frozen=True)
class DestroyedEvent(Event):
    """msg=5: 实例已销毁。"""
    pass
