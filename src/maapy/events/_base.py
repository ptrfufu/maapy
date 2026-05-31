"""事件基类。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Event:
    """所有回调事件的基类。"""
    msg: int
    uuid: str


@dataclass(frozen=True)
class TaskChainMixin:
    """任务链消息的公共字段。"""
    taskchain: str
    taskid: int


@dataclass(frozen=True)
class SubTaskMixin(TaskChainMixin):
    """子任务消息的公共字段。"""
    subtask: str
    class_name: str  # C++ 类符号名
