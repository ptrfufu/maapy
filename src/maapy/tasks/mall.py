from __future__ import annotations

from dataclasses import dataclass, field

from ._base import TaskBase


@dataclass
class MallTask(TaskBase):
    visit_friends: bool = True
    shopping: bool = True
    buy_first: list[str] = field(default_factory=list)
    blacklist: list[str] = field(default_factory=list)
    force_shopping_if_credit_full: bool = False
    only_buy_discount: bool = False
    reserve_max_credit: bool = False
    credit_fight: bool = False
    formation_index: int = 0
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Mall"
