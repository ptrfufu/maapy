from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import RoguelikeThemeCode as RoguelikeTheme
from ._base import TaskBase


@dataclass
class RoguelikeTask(TaskBase):
    theme: RoguelikeTheme = "Phantom"
    mode: int = 0
    difficulty: int = 0
    starts_count: int = 2147483647
    investment_enabled: bool = True
    investment_with_more_score: bool = False
    investments_count: int = 2147483647
    stop_when_investment_full: bool = False
    collectible_mode_shopping: bool = False
    collectible_mode_squad: str = ""
    squad: str = ""
    roles: str = ""
    core_char: str = ""
    collectible_mode_start_list: dict[str, bool] = field(default_factory=dict)
    first_floor_foldartal: str = ""
    start_foldartal_list: list[str] = field(default_factory=list)
    expected_collapsal_paradigms: list[str] = field(default_factory=list)
    use_support: bool = False
    use_nonfriend_support: bool = False
    refresh_trader_with_dice: bool = False
    monthly_squad_auto_iterate: bool = False
    monthly_squad_check_comms: bool = False
    deep_exploration_auto_iterate: bool = False
    find_playtime_target: int | None = None
    stop_at_final_boss: bool = False
    stop_at_max_level: bool = False
    start_with_elite_two: bool = False
    only_start_with_elite_two: bool = False
    start_with_seed: str | None = None
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Roguelike"

    def to_params(self, *, validate: bool = True):
        params = super().to_params(validate=validate)
        params.pop("find_playtime_target", None)
        if self.find_playtime_target is not None:
            params["find_playTime_target"] = self.find_playtime_target
        return params

    def to_patch(self, *, validate: bool = False):
        params = super().to_patch(validate=validate)
        params.pop("find_playtime_target", None)
        if self.find_playtime_target is not None:
            params["find_playTime_target"] = self.find_playtime_target
        return params
