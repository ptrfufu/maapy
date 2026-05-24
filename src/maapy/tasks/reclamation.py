from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ._base import TaskBase

ReclamationTheme = Literal["Fire", "Tales", "RelaunchAnchor"]


@dataclass
class ReclamationTask(TaskBase):
    theme: ReclamationTheme = "Tales"
    mode: int = 0
    tools_to_craft: list[str] = field(default_factory=lambda: ["荧光棒"])
    increment_mode: int = 0  # 0=递增, 1=递减
    num_craft_batches: int = 16
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Reclamation"
