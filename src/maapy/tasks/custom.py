from __future__ import annotations

from dataclasses import dataclass, field

from .._json import JsonDict
from ..exceptions import MaaValidationError
from ._base import JsonModel, TaskBase


@dataclass
class CustomTask(TaskBase):
    task_names: list[str] = field(default_factory=list)
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        if not partial:
            self._require(self.task_names, "task_names")

    @classmethod
    def task_type(cls) -> str:
        return "Custom"


@dataclass
class SingleStepCopilotStageDetails(JsonModel):
    stage_name: str = ""
    stage: str = ""

    def validate(self) -> None:
        if not self.stage_name and not self.stage:
            raise MaaValidationError("details.stage_name cannot be empty")

    def to_json(self) -> JsonDict:
        result: JsonDict = {"stage_name": self.stage_name or self.stage}
        return result


@dataclass
class SingleStepCopilotAction(JsonModel):
    type: str = ""
    kills: int = 0
    cost_changes: int = 0
    name: str = ""
    location: tuple[int, int] | list[int] | None = None
    direction: str = "Right"
    skill_usage: int = 0
    skill_times: int = 1
    pre_delay: int = 0
    post_delay: int | None = None
    rear_delay: int | None = None

    def validate(self) -> None:
        if not self.type:
            raise MaaValidationError("details.type cannot be empty")
        if self.location is not None and len(self.location) != 2:
            raise MaaValidationError("details.location must contain exactly two integers")


@dataclass
class SingleStepTask(TaskBase):
    type: str = "copilot"
    subtype: str = ""
    subtask: str = ""  # subtype 的废弃别名，保留以兼容旧代码
    details: SingleStepCopilotStageDetails | SingleStepCopilotAction | None = None
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        subtype = self.subtype or self.subtask
        if not partial:
            self._require(self.type, "type")
            self._require(subtype, "subtype")
        if subtype == "stage" and self.details is None:
            raise MaaValidationError("stage subtype requires details")
        if subtype == "action" and self.details is None:
            raise MaaValidationError("action subtype requires details")

    @classmethod
    def task_type(cls) -> str:
        return "SingleStep"

    def to_params(self, *, validate: bool = True):
        params = super().to_params(validate=validate)
        params.pop("subtask", None)
        params["subtype"] = self.subtype or self.subtask
        return params

    def to_patch(self, *, validate: bool = False):
        params = super().to_patch(validate=validate)
        params.pop("subtask", None)
        subtype = self.subtype or self.subtask
        if subtype:
            params["subtype"] = subtype
        return params


@dataclass
class VideoRecognitionTask(TaskBase):
    filename: str = ""
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        if not partial:
            self._require(self.filename, "filename")

    @classmethod
    def task_type(cls) -> str:
        return "VideoRecognition"
