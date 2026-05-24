from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ._base import TaskBase

ClientType = Literal["Official", "Bilibili", "txwy", "YoStarEN", "YoStarJP", "YoStarKR"]


@dataclass
class StartUpTask(TaskBase):
    client_type: ClientType | None = None
    start_game_enabled: bool = False
    account_name: str = ""
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "StartUp"
