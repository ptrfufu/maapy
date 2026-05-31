"""全局和任务链回调的解析逻辑"""

from __future__ import annotations

import msgspec

from .._json import JsonDict
from ..constants import AsstMsg
from ..events._base import Event
from ..events.global_events import (
    AllTasksCompletedEvent,
    AsyncCallInfoEvent,
    AttachWindowAsyncCallInfoEvent,
    CallbackErrorEvent,
    ClickAsyncCallInfoEvent,
    ConnectAsyncCallInfoEvent,
    ConnectFailedConnectionEvent,
    ConnectedConnectionEvent,
    ConnectionEvent,
    DestroyedEvent,
    DisconnectConnectionEvent,
    FastestWayToScreencapConnectionEvent,
    InitFailedEvent,
    InternalErrorEvent,
    ReconnectedConnectionEvent,
    ReconnectingConnectionEvent,
    ReportRequestEvent,
    ResolutionErrorConnectionEvent,
    ResolutionGotConnectionEvent,
    ResolutionInfoConnectionEvent,
    ScreencapAsyncCallInfoEvent,
    ScreencapCostConnectionEvent,
    ScreencapFailedConnectionEvent,
    ScreencapMethodAlternative,
    TouchModeNotAvailableConnectionEvent,
    UnknownAsyncCallInfoEvent,
    UnsupportedPlayToolsConnectionEvent,
    UnsupportedResolutionConnectionEvent,
    UuidGotConnectionEvent,
)
from ..events.taskchain_events import RoutingRestartTaskChainEvent, TaskChainExtraInfoEvent
from .common import _EventFactory, _MsgParser, _decode_struct
from .payloads import (
    AllTasksCompletedPayload,
    AsyncCallInfoPayload,
    ConnectionInfoPayload,
    InitFailedPayload,
    ReportRequestPayload,
    ScreencapAlternativePayload,
    TaskChainPayload,
)


class GlobalTaskchainParsingMixin:
    """集中处理全局事件和任务链事件的 JSON 解析"""

    _msg_dispatch: dict[AsstMsg, _MsgParser]
    _taskchain_event_classes: dict[AsstMsg, _EventFactory]

    def _parse_and_route(self, msg: int, data: JsonDict) -> Event | None:
        try:
            msg_id = AsstMsg(msg)
        except ValueError:
            raise msgspec.ValidationError(f"unknown callback msg: {msg}") from None
        parser = self._msg_dispatch.get(msg_id)
        if parser is not None:
            return parser(msg_id, data)
        raise msgspec.ValidationError(f"unhandled callback msg: {msg_id.name}") from None

    def _callback_error(self, msg: int, source: str, exc: BaseException) -> CallbackErrorEvent:
        return CallbackErrorEvent(
            msg=msg,
            uuid="",
            source=source,
            error=f"{type(exc).__name__}: {exc}",
        )

    def _parse_internal_error(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        del data
        return InternalErrorEvent(msg=int(msg_id), uuid="")

    def _parse_init_failed(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, InitFailedPayload, "callback")
        return InitFailedEvent(
            msg=int(msg_id),
            uuid="",
            what=payload.what,
            why=payload.why,
        )

    def _parse_connection_info(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, ConnectionInfoPayload, "callback")
        details = payload.details
        what = payload.what
        common_kwargs = {
            "msg": int(msg_id),
            "uuid": payload.uuid,
            "what": what,
            "why": payload.why,
            "connected": what in ("Connected", "UuidGot"),
        }

        if what == "ConnectFailed":
            return ConnectFailedConnectionEvent(
                **common_kwargs,
                adb=details.adb,
                address=details.address,
                config=details.config,
                adb_output=details.adb_output,
            )
        if what == "Connected":
            return ConnectedConnectionEvent(
                **common_kwargs,
                adb=details.adb,
                address=details.address,
                config=details.config,
            )
        if what == "UuidGot":
            return UuidGotConnectionEvent(
                **common_kwargs,
                adb=details.adb,
                address=details.address,
                config=details.config,
                device_uuid=details.uuid,
            )
        if what == "UnsupportedResolution":
            return UnsupportedResolutionConnectionEvent(
                **common_kwargs,
                width=details.width or payload.width,
                height=details.height or payload.height,
            )
        if what == "ResolutionInfo":
            return ResolutionInfoConnectionEvent(
                **common_kwargs,
                width=details.width or payload.width,
                height=details.height or payload.height,
            )
        if what == "ResolutionGot":
            return ResolutionGotConnectionEvent(
                **common_kwargs,
                adb=details.adb,
                address=details.address,
                config=details.config,
                width=details.width or payload.width,
                height=details.height or payload.height,
            )
        if what == "ResolutionError":
            return ResolutionErrorConnectionEvent(
                **common_kwargs,
                adb=details.adb,
                address=details.address,
                config=details.config,
                width=details.width or payload.width,
                height=details.height or payload.height,
            )
        if what == "Reconnecting":
            return ReconnectingConnectionEvent(
                **common_kwargs,
                reconnect=details.reconnect,
                cmd=details.cmd,
                times=details.times,
            )
        if what == "Reconnected":
            return ReconnectedConnectionEvent(
                **common_kwargs,
                reconnect=details.reconnect,
                cmd=details.cmd,
                times=details.times,
            )
        if what == "Disconnect":
            return DisconnectConnectionEvent(
                **common_kwargs,
                reconnect=details.reconnect,
                cmd=details.cmd,
                times=details.times,
            )
        if what == "ScreencapFailed":
            return ScreencapFailedConnectionEvent(**common_kwargs)
        if what == "TouchModeNotAvailable":
            return TouchModeNotAvailableConnectionEvent(
                **common_kwargs,
                adb=details.adb,
                address=details.address,
                config=details.config,
            )
        if what == "FastestWayToScreencap":
            return FastestWayToScreencapConnectionEvent(
                **common_kwargs,
                method=details.method,
                cost=details.cost,
                alternatives=[_screencap_alternative(item) for item in details.alternatives],
            )
        if what == "ScreencapCost":
            return ScreencapCostConnectionEvent(
                **common_kwargs,
                min_cost=details.min_cost,
                max_cost=details.max_cost,
                avg_cost=details.avg_cost,
                fault_times=details.fault_times,
            )
        if what == "UnsupportedPlayTools":
            return UnsupportedPlayToolsConnectionEvent(**common_kwargs)
        raise msgspec.ValidationError(f"unknown ConnectionInfo what: {what}") from None

    def _parse_all_tasks_completed(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, AllTasksCompletedPayload, "callback")
        return AllTasksCompletedEvent(
            msg=int(msg_id),
            uuid=payload.uuid,
            taskchain=payload.taskchain,
            finished_tasks=list(payload.finished_tasks),
        )

    def _parse_async_call_info(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, AsyncCallInfoPayload, "callback")
        common_kwargs = {
            "msg": int(msg_id),
            "uuid": payload.uuid,
            "what": payload.what,
            "async_call_id": payload.async_call_id,
            "ret": payload.details.ret,
            "cost": payload.details.cost,
        }
        what = payload.what
        if what == "Connect":
            return ConnectAsyncCallInfoEvent(**common_kwargs)
        if what == "AttachWindow":
            return AttachWindowAsyncCallInfoEvent(**common_kwargs)
        if what == "Click":
            return ClickAsyncCallInfoEvent(**common_kwargs)
        if what == "Screencap":
            return ScreencapAsyncCallInfoEvent(**common_kwargs)
        if what == "Unknown":
            return UnknownAsyncCallInfoEvent(**common_kwargs)
        raise msgspec.ValidationError(f"unknown AsyncCallInfo what: {what}") from None

    def _parse_destroyed(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, TaskChainPayload, "callback")
        return DestroyedEvent(msg=int(msg_id), uuid=payload.uuid)

    def _parse_report_request(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, ReportRequestPayload, "callback")
        return ReportRequestEvent(
            msg=int(msg_id),
            uuid=payload.uuid,
            url=payload.url,
            headers=dict(payload.headers),
            body=payload.body,
            subtask=payload.subtask,
        )

    def _parse_taskchain(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, TaskChainPayload, "callback")
        if msg_id == AsstMsg.TASK_CHAIN_EXTRA_INFO:
            common_kwargs = {
                "msg": int(msg_id),
                "uuid": payload.uuid,
                "taskchain": payload.taskchain,
                "taskid": payload.taskid,
                "what": payload.what,
                "why": payload.why,
            }
            if payload.what == "RoutingRestart":
                return RoutingRestartTaskChainEvent(
                    **common_kwargs,
                    node_cost=payload.node_cost,
                )
            return TaskChainExtraInfoEvent(**common_kwargs)

        event_class = self._taskchain_event_classes.get(msg_id)
        if event_class is None:
            raise msgspec.ValidationError(f"unhandled taskchain msg: {msg_id.name}")
        return event_class(
            msg=int(msg_id),
            uuid=payload.uuid,
            taskchain=payload.taskchain,
            taskid=payload.taskid,
        )


def _screencap_alternative(item: ScreencapAlternativePayload) -> ScreencapMethodAlternative:
    return ScreencapMethodAlternative(method=item.method, cost=item.cost)
