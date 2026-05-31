from ._base import JsonModel, TaskBase
from .award import AwardTask
from .closedown import CloseDownTask
from .copilot import (
    CopilotMultiTask,
    CopilotTask,
    CopilotUserAdditional,
    ParadoxCopilotTask,
    SSSCopilotTask,
)
from .custom import (
    CustomTask,
    SingleStepCopilotAction,
    SingleStepCopilotStageDetails,
    SingleStepTask,
    VideoRecognitionTask,
)
from .debug import DebugTask
from .depot import DepotTask
from .fight import FightTask
from .infrast import InfrastTask
from .mall import MallTask
from .operbox import OperBoxTask
from .reclamation import ReclamationTask
from .recruit import RecruitTask, RecruitmentTime
from .roguelike import RoguelikeTask
from .startup import StartUpTask

__all__ = [
    "JsonModel",
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
    "ParadoxCopilotTask",
    "DebugTask",
    "CopilotMultiTask",
    "CopilotUserAdditional",
    "SingleStepCopilotStageDetails",
    "SingleStepCopilotAction",
    "RecruitmentTime",
    "DepotTask",
    "OperBoxTask",
    "ReclamationTask",
    "CustomTask",
    "SingleStepTask",
    "VideoRecognitionTask",
]
