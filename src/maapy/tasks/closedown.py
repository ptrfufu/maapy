from __future__ import annotations

from dataclasses import dataclass

from ..constants import ClientCode as ClientType
from ._base import TaskBase


@dataclass
class CloseDownTask(TaskBase):
    client_type: ClientType | None = None
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "CloseDown"
