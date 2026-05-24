from __future__ import annotations

from dataclasses import dataclass, field

from ._base import TaskBase


@dataclass
class CopilotTask(TaskBase):
    filename: str = ""  # 作业 JSON 路径（与 copilot_list 二选一）
    copilot_list: list[dict] = field(default_factory=list)
    loop_times: int = 1
    use_sanity_potion: bool = False
    formation: bool = False
    formation_index: int = 0
    user_additional: list[dict] = field(default_factory=list)
    add_trust: bool = False
    ignore_requirements: bool = False
    support_unit_usage: int = 0  # 0~3
    support_unit_name: str = ""
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Copilot"


@dataclass
class SSSCopilotTask(TaskBase):
    filename: str = ""
    loop_times: int = 1
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "SSSCopilot"
