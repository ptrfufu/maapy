from __future__ import annotations

from dataclasses import dataclass, field

from ..constants import DroneCode as DroneUsage, FacilityCode as FacilityType
from ._base import TaskBase


@dataclass
class InfrastTask(TaskBase):
    facility: list[FacilityType] = field(default_factory=list)  # 必填
    mode: int = 0  # 0=默认, 10000=自定义, 20000=轮换
    drones: DroneUsage = "_NotUse"
    threshold: float = 0.3
    replenish: bool = False
    dorm_notstationed_enabled: bool = False
    dorm_trust_enabled: bool = False
    reception_message_board: bool = True
    reception_clue_exchange: bool = True
    reception_send_clue: bool = True
    filename: str = ""  # mode=10000 时必填
    plan_index: int = 0  # mode=10000 时必填
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Infrast"
