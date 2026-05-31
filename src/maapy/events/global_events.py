"""全局回调事件"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._base import Event


@dataclass(slots=True, frozen=True)
class InternalErrorEvent(Event):
    """msg=0"""


@dataclass(slots=True, frozen=True)
class CallbackErrorEvent(Event):
    """Python 回调层错误"""

    source: str = ""
    error: str = ""


@dataclass(slots=True, frozen=True)
class InitFailedEvent(Event):
    """msg=1"""

    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class ConnectionEvent(Event):
    """msg=2"""

    what: str = ""
    why: str = ""
    connected: bool = False


@dataclass(slots=True, frozen=True)
class ConnectionContextEvent(ConnectionEvent):
    adb: str = ""
    address: str = ""
    config: str = ""


@dataclass(slots=True, frozen=True)
class ConnectFailedConnectionEvent(ConnectionContextEvent):
    adb_output: str = ""


@dataclass(slots=True, frozen=True)
class ConnectedConnectionEvent(ConnectionContextEvent):
    connected: bool = True


@dataclass(slots=True, frozen=True)
class UuidGotConnectionEvent(ConnectionContextEvent):
    connected: bool = True
    device_uuid: str = ""


@dataclass(slots=True, frozen=True)
class UnsupportedResolutionConnectionEvent(ConnectionEvent):
    width: int = 0
    height: int = 0


@dataclass(slots=True, frozen=True)
class ResolutionInfoConnectionEvent(ConnectionEvent):
    width: int = 0
    height: int = 0


@dataclass(slots=True, frozen=True)
class ResolutionGotConnectionEvent(ConnectionContextEvent):
    width: int = 0
    height: int = 0


@dataclass(slots=True, frozen=True)
class ResolutionErrorConnectionEvent(ConnectionContextEvent):
    width: int = 0
    height: int = 0


@dataclass(slots=True, frozen=True)
class ReconnectingConnectionEvent(ConnectionEvent):
    reconnect: str = ""
    cmd: str = ""
    times: int = 0


@dataclass(slots=True, frozen=True)
class ReconnectedConnectionEvent(ReconnectingConnectionEvent):
    pass


@dataclass(slots=True, frozen=True)
class DisconnectConnectionEvent(ReconnectingConnectionEvent):
    pass


@dataclass(slots=True, frozen=True)
class ScreencapFailedConnectionEvent(ConnectionEvent):
    pass


@dataclass(slots=True, frozen=True)
class TouchModeNotAvailableConnectionEvent(ConnectionContextEvent):
    pass


@dataclass(slots=True, frozen=True)
class ScreencapMethodAlternative:
    method: str = ""
    cost: int = 0


@dataclass(slots=True, frozen=True)
class FastestWayToScreencapConnectionEvent(ConnectionEvent):
    method: str = ""
    cost: int = 0
    alternatives: list[ScreencapMethodAlternative] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ScreencapCostConnectionEvent(ConnectionEvent):
    min_cost: int = 0
    max_cost: int = 0
    avg_cost: int = 0
    fault_times: int = 0


@dataclass(slots=True, frozen=True)
class UnsupportedPlayToolsConnectionEvent(ConnectionEvent):
    pass


@dataclass(slots=True, frozen=True)
class AllTasksCompletedEvent(Event):
    """msg=3"""

    taskchain: str = ""
    finished_tasks: list[int] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class AsyncCallInfoEvent(Event):
    """msg=4"""

    what: str = ""
    async_call_id: int = 0
    ret: bool = False
    cost: int = 0


@dataclass(slots=True, frozen=True)
class ConnectAsyncCallInfoEvent(AsyncCallInfoEvent):
    pass


@dataclass(slots=True, frozen=True)
class AttachWindowAsyncCallInfoEvent(AsyncCallInfoEvent):
    pass


@dataclass(slots=True, frozen=True)
class ClickAsyncCallInfoEvent(AsyncCallInfoEvent):
    pass


@dataclass(slots=True, frozen=True)
class ScreencapAsyncCallInfoEvent(AsyncCallInfoEvent):
    pass


@dataclass(slots=True, frozen=True)
class UnknownAsyncCallInfoEvent(AsyncCallInfoEvent):
    pass


@dataclass(slots=True, frozen=True)
class DestroyedEvent(Event):
    """msg=5"""


@dataclass(slots=True, frozen=True)
class ReportRequestEvent(Event):
    """msg=30000"""

    url: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""
    subtask: str = ""
