"""任务链回调事件"""

from __future__ import annotations

from dataclasses import dataclass

from ._base import Event, TaskChainMixin


@dataclass(slots=True, frozen=True)
class TaskChainErrorEvent(Event, TaskChainMixin):
    """msg=10000"""


@dataclass(slots=True, frozen=True)
class TaskChainStartEvent(Event, TaskChainMixin):
    """msg=10001"""


@dataclass(slots=True, frozen=True)
class TaskChainCompletedEvent(Event, TaskChainMixin):
    """msg=10002"""


@dataclass(slots=True, frozen=True)
class TaskChainExtraInfoEvent(Event, TaskChainMixin):
    """msg=10003"""

    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class RoutingRestartTaskChainEvent(TaskChainExtraInfoEvent):
    node_cost: int = 0


@dataclass(slots=True, frozen=True)
class TaskChainStoppedEvent(Event, TaskChainMixin):
    """msg=10004"""
