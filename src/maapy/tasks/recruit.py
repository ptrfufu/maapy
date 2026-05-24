from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ._base import TaskBase

Server = Literal["CN", "US", "JP", "KR"]


@dataclass
class RecruitTask(TaskBase):
    select: list[int] | None = None  # 必填: 会去选中的 Tag 等级
    confirm: list[int] | None = None  # 必填: 会去确认的 Tag 等级
    refresh: bool = False
    first_tags: list[str] = field(default_factory=list)
    extra_tags_mode: int = 0  # 0=默认, 1=选3个, 2=尽量多选
    times: int = 0  # 0=一次
    set_time: bool = True
    expedite: bool = False
    expedite_times: int = 0
    skip_robot: bool = True
    recruitment_time: dict[str, int] = field(default_factory=dict)  # {"3":540,"4":540}
    report_to_penguin: bool = False
    penguin_id: str = ""
    report_to_yituliu: bool = False
    yituliu_id: str = ""
    server: Server = "CN"
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Recruit"
