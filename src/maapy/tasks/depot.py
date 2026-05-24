from __future__ import annotations

from dataclasses import dataclass

from ._base import TaskBase


@dataclass
class DepotTask(TaskBase):
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Depot"
