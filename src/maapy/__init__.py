"""maapy——基于 CFFI 的 MaaCore.dll Python 绑定。

使用方式:
    from maapy import MaaClient
    from maapy.tasks import FightTask, StartUpTask
    from maapy.events import StageDropsEvent, ConnectionEvent

    MaaClient.load(core_dir="F:/maa")
    client = MaaClient()
    client.connect("127.0.0.1:5555")
    task = client.append(FightTask(stage="1-7", times=10), tag="farm")
    client.start()
    task.wait()
"""

from .client import MaaClient, TaskHandle, TaskResult, TaskStatus
from .constants import (
    AsstMsg,
    AsstTaskType,
    ClientType,
    ConnectionWhat,
    Facility,
    InstanceOptionKey,
    ReclamationTheme,
    RoguelikeTheme,
    Server,
    StaticOptionKey,
    SubTaskWhat,
)
from .events import (
    AllTasksCompletedEvent,
    AsyncCallInfoEvent,
    ConnectionEvent,
    StageDropsEvent,
    TaskChainCompletedEvent,
    TaskChainErrorEvent,
    TaskChainStartEvent,
)
from .exceptions import (
    MaaCallbackError,
    MaaConnectionError,
    MaaDataError,
    MaaError,
    MaaLoadError,
    MaaTaskError,
)

__all__ = [
    "MaaClient",
    "TaskHandle",
    "TaskResult",
    "TaskStatus",
    "AsstMsg",
    "AsstTaskType",
    "MaaError",
    "MaaLoadError",
    "MaaConnectionError",
    "MaaTaskError",
    "MaaDataError",
    "MaaCallbackError",
]
