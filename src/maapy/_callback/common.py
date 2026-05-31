"""回调解析共用的辅助函数和类型别名"""

from __future__ import annotations

from typing import Callable, TypeAlias, TypedDict, TypeVar

import msgspec

from .._json import JsonDict, as_json_dict
from ..constants import AsstMsg
from ..events._base import Event

_MsgParser: TypeAlias = Callable[[AsstMsg, JsonDict], Event]
_EventFactory: TypeAlias = Callable[..., Event]
_SubTaskExtraParser: TypeAlias = Callable[..., Event]
_T = TypeVar("_T")


class _SubtaskEventKwargs(TypedDict):
    msg: int
    uuid: str
    subtask: str
    class_name: str
    taskchain: str
    taskid: int
    what: str
    why: str


def _decode_struct(value: object, model: type[_T], field_name: str) -> _T:
    try:
        data = as_json_dict(value)
    except msgspec.ValidationError as exc:
        raise msgspec.ValidationError(f"{field_name}: {exc}") from exc
    try:
        return msgspec.convert(data, type=model)
    except msgspec.ValidationError as exc:
        raise msgspec.ValidationError(f"{field_name}: {exc}") from exc


__all__ = [
    "_EventFactory",
    "_MsgParser",
    "_SubTaskExtraParser",
    "_SubtaskEventKwargs",
    "_decode_struct",
]
