"""子任务回调分发与兜底解析"""

from __future__ import annotations

from typing import Unpack

import msgspec

from .._json import JsonDict
from ..constants import AsstMsg
from ..events._base import Event
from .common import _EventFactory, _SubTaskExtraParser, _SubtaskEventKwargs, _decode_struct
from .payloads import SubTaskPayload, SubTaskStartDetails
from .subtask_structured import StructuredSubtaskParsingMixin


class SubtaskParsingMixin(StructuredSubtaskParsingMixin):
    """负责子任务事件的总入口和路由"""

    _subtask_event_classes: dict[AsstMsg, _EventFactory]
    _subtask_named_event_classes: dict[tuple[AsstMsg, str], _EventFactory]
    _subtask_extra_parsers: dict[str, _SubTaskExtraParser]
    _subtask_error_parsers: dict[str, _SubTaskExtraParser]

    def _parse_subtask(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, SubTaskPayload, "callback")
        msg = int(msg_id)
        common_kwargs: _SubtaskEventKwargs = {
            "msg": msg,
            "uuid": payload.uuid,
            "subtask": payload.subtask,
            "class_name": payload.class_name,
            "taskchain": payload.taskchain,
            "taskid": payload.taskid,
            "what": payload.what,
            "why": payload.why,
        }

        if msg_id == AsstMsg.SUB_TASK_EXTRA_INFO:
            return self._parse_subtask_extra(data, **common_kwargs)

        if msg_id == AsstMsg.SUB_TASK_ERROR:
            parser = self._subtask_error_parsers.get(common_kwargs["what"])
            if parser is not None:
                return parser(data, **common_kwargs)

        event_class = self._subtask_named_event_classes.get((msg_id, common_kwargs["what"]))
        if event_class is None:
            event_class = self._subtask_event_classes.get(msg_id)
        if event_class is None:
            raise msgspec.ValidationError(f"unhandled subtask msg: {msg_id.name}") from None

        if msg_id == AsstMsg.SUB_TASK_START:
            details = _decode_struct(data.get("details"), SubTaskStartDetails, "details")
            return event_class(
                **common_kwargs,
                task_name=details.task,
            )

        return event_class(**common_kwargs)

    def _parse_subtask_extra(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        parser = self._subtask_extra_parsers.get(kwargs["what"])
        if parser is not None:
            return parser(data, **kwargs)

        if kwargs["subtask"] == "ProcessTask":
            return self._parse_process_task(data, **kwargs)

        raise msgspec.ValidationError(f"unknown subtask extra what: {kwargs['what']}") from None
