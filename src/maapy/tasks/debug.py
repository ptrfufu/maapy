from __future__ import annotations

from dataclasses import dataclass

from ._base import TaskBase


@dataclass
class DebugTask(TaskBase):
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Debug"
