from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import TaskBase


@dataclass
class CustomTask(TaskBase):
    task_names: list[str] = field(default_factory=list)  # 必填
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Custom"


@dataclass
class SingleStepTask(TaskBase):
    type: str = "copilot"  # 目前仅支持 "copilot"
    subtask: str = ""  # stage / start / action
    details: dict[str, Any] = field(default_factory=dict)
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "SingleStep"


@dataclass
class VideoRecognitionTask(TaskBase):
    filename: str = ""  # 视频文件路径，必填
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "VideoRecognition"
