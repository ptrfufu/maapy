from __future__ import annotations

from dataclasses import dataclass

from ._base import TaskBase
from .startup import ClientType


@dataclass
class CloseDownTask(TaskBase):
    client_type: ClientType | None = None
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "CloseDown"
