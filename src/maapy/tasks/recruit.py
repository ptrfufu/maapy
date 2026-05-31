from __future__ import annotations

from dataclasses import dataclass, field

from .._json import JsonDict
from ..constants import ServerCode as Server
from ._base import JsonModel, TaskBase


@dataclass
class RecruitmentTime(JsonModel):
    level3: int = 540
    level4: int = 540
    level5: int = 540
    level6: int = 540

    def to_json(self) -> JsonDict:
        result: JsonDict = {
            "3": self.level3,
            "4": self.level4,
            "5": self.level5,
            "6": self.level6,
        }
        return result


@dataclass
class RecruitTask(TaskBase):
    select: list[int] | None = None
    confirm: list[int] | None = None
    refresh: bool = False
    force_refresh: bool = True
    first_tags: list[str] = field(default_factory=list)
    extra_tags_mode: int = 0
    times: int = 0
    set_time: bool = True
    expedite: bool = False
    expedite_times: int = 0
    preserve_tags: list[str] = field(default_factory=list)
    skip_robot: bool | None = None
    skip_tags: list[str] = field(default_factory=list)
    recruitment_time: RecruitmentTime = field(default_factory=RecruitmentTime)
    report_to_penguin: bool = False
    penguin_id: str = ""
    report_to_yituliu: bool = False
    yituliu_id: str = ""
    server: Server = "CN"
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        if not partial:
            self._require(self.select, "select")
            self._require(self.confirm, "confirm")

    @classmethod
    def task_type(cls) -> str:
        return "Recruit"

    def to_params(self, *, validate: bool = True):
        params = super().to_params(validate=validate)
        if self.preserve_tags:
            params["preserve_tags"] = list(self.preserve_tags)
        elif self.skip_tags:
            params["preserve_tags"] = list(self.skip_tags)
        else:
            params.pop("preserve_tags", None)
        params.pop("skip_tags", None)
        if self.skip_robot is None:
            params.pop("skip_robot", None)
        return params

    def to_patch(self, *, validate: bool = False):
        params = super().to_patch(validate=validate)
        if self.preserve_tags:
            params["preserve_tags"] = list(self.preserve_tags)
        elif self.skip_tags:
            params["preserve_tags"] = list(self.skip_tags)
        params.pop("skip_tags", None)
        if self.skip_robot is None:
            params.pop("skip_robot", None)
        return params
