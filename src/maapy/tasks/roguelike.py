from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ._base import TaskBase

RoguelikeTheme = Literal["Phantom", "Mizuki", "Sami", "Sarkaz", "JieGarden"]


@dataclass
class RoguelikeTask(TaskBase):
    theme: RoguelikeTheme = "Phantom"
    mode: int = 0
    squad: str = ""
    roles: str = ""
    core_char: str = ""
    use_support: bool = False
    use_nonfriend_support: bool = False
    starts_count: int = 2147483647
    difficulty: int = 0
    stop_at_final_boss: bool = False
    stop_at_max_level: bool = False
    investment_enabled: bool = True
    investments_count: int = 2147483647
    stop_when_investment_full: bool = False
    investment_with_more_score: bool = False
    start_with_elite_two: bool = False
    only_start_with_elite_two: bool = False
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Roguelike"
