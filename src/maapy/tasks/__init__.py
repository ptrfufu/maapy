"""任务构造器——所有任务类型的 dataclass 定义。

每个类对应一种 AsstAppendTask 的 type 参数，

"""

from ._base import TaskBase
from .award import AwardTask
from .closedown import CloseDownTask
from .copilot import CopilotTask, SSSCopilotTask
from .custom import CustomTask, SingleStepTask, VideoRecognitionTask
from .depot import DepotTask
from .fight import FightTask
from .infrast import InfrastTask
from .mall import MallTask
from .operbox import OperBoxTask
from .reclamation import ReclamationTask
from .recruit import RecruitTask
from .roguelike import RoguelikeTask
from .startup import StartUpTask

__all__ = [
    "TaskBase",
    "StartUpTask",
    "CloseDownTask",
    "FightTask",
    "RecruitTask",
    "InfrastTask",
    "MallTask",
    "AwardTask",
    "RoguelikeTask",
    "CopilotTask",
    "SSSCopilotTask",
    "DepotTask",
    "OperBoxTask",
    "ReclamationTask",
    "CustomTask",
    "SingleStepTask",
    "VideoRecognitionTask",
]
