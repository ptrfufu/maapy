from __future__ import annotations

from dataclasses import dataclass

from ._base import TaskBase


@dataclass
class AwardTask(TaskBase):
    award: bool = True
    mail: bool = False
    recruit: bool = False
    orundum: bool = False
    mining: bool = False
    specialaccess: bool = False
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Award"
