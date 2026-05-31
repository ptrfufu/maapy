from __future__ import annotations

from dataclasses import dataclass, field

from ..exceptions import MaaValidationError
from ._base import JsonModel, TaskBase


@dataclass
class CopilotMultiTask(JsonModel):
    filename: str = ""
    stage_name: str = ""
    is_raid: bool = False

    def validate(self) -> None:
        if not self.filename:
            raise MaaValidationError("copilot_list[].filename cannot be empty")


@dataclass
class CopilotUserAdditional(JsonModel):
    name: str = ""
    skill: int = 0
    module: int = 0

    def validate(self) -> None:
        if not self.name:
            raise MaaValidationError("user_additional[].name cannot be empty")
        TaskBase._require_range(self.skill, "user_additional[].skill", 0, 3)
        TaskBase._require_range(self.module, "user_additional[].module", -1, 4)


@dataclass
class CopilotTask(TaskBase):
    filename: str = ""
    copilot_list: list[CopilotMultiTask] = field(default_factory=list)
    loop_times: int = 1
    use_sanity_potion: bool = False
    formation: bool = False
    formation_index: int = 0
    user_additional: list[CopilotUserAdditional] = field(default_factory=list)
    add_trust: bool = False
    ignore_requirements: bool = False
    support_unit_usage: int = 0
    support_unit_name: str = ""
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        has_filename = bool(self.filename)
        has_list = bool(self.copilot_list)
        if not partial and has_filename == has_list:
            raise MaaValidationError("filename and copilot_list must choose exactly one")
        self._require_range(self.support_unit_usage, "support_unit_usage", 0, 3)

    @classmethod
    def task_type(cls) -> str:
        return "Copilot"


@dataclass
class SSSCopilotTask(TaskBase):
    filename: str = ""
    loop_times: int = 1
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        if not partial:
            self._require(self.filename, "filename")

    @classmethod
    def task_type(cls) -> str:
        return "SSSCopilot"


@dataclass
class ParadoxCopilotTask(TaskBase):
    filename: str = ""
    task_list: list[str] = field(default_factory=list)
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        has_filename = bool(self.filename)
        has_list = bool(self.task_list)
        if not partial and has_filename == has_list:
            raise MaaValidationError("filename and task_list must choose exactly one")

    @classmethod
    def task_type(cls) -> str:
        return "ParadoxCopilot"

    def to_params(self, *, validate: bool = True):
        params = super().to_params(validate=validate)
        params.pop("task_list", None)
        if self.task_list:
            params["list"] = list(self.task_list)
        return params

    def to_patch(self, *, validate: bool = False):
        params = super().to_patch(validate=validate)
        params.pop("task_list", None)
        if self.task_list:
            params["list"] = list(self.task_list)
        return params
