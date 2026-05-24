"""任务链消息事件 (msg 10000-10004)。"""

from __future__ import annotations

from dataclasses import dataclass

from ._base import Event, TaskChainMixin


@dataclass(slots=True, frozen=True)
class TaskChainErrorEvent(Event, TaskChainMixin):
    """msg=10000: 任务链执行/识别错误。"""
    pass


@dataclass(slots=True, frozen=True)
class TaskChainStartEvent(Event, TaskChainMixin):
    """msg=10001: 任务链开始。"""
    pass


@dataclass(slots=True, frozen=True)
class TaskChainCompletedEvent(Event, TaskChainMixin):
    """msg=10002: 任务链完成。"""
    pass


@dataclass(slots=True, frozen=True)
class TaskChainExtraInfoEvent(Event, TaskChainMixin):
    """msg=10003: 任务链额外信息。"""
    pass


@dataclass(slots=True, frozen=True)
class TaskChainStoppedEvent(Event, TaskChainMixin):
    """msg=10004: 任务链手动停止。"""
    pass
