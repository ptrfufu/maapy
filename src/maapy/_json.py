"""msgspec 驱动的 JSON 边界工具"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypeAlias, cast

import msgspec


JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonDict: TypeAlias = dict[str, JsonValue]


def encode_json(obj: Mapping[str, JsonValue]) -> bytes:
    """把 Python JSON 对象编码给 MaaCore"""
    return msgspec.json.encode(obj)


def decode_json(data: bytes | bytearray | memoryview | str) -> JsonValue:
    """解码 MaaCore 返回的任意 JSON payload"""
    return msgspec.json.decode(data)


def decode_json_dict(data: bytes | bytearray | memoryview | str) -> JsonDict:
    """解码 JSON 对象，拒绝数组和标量"""
    decoded = decode_json(data)
    if not isinstance(decoded, dict):
        raise msgspec.ValidationError("expected JSON object")
    return cast(JsonDict, decoded)


def as_json_dict(value: object) -> JsonDict:
    """把动态值收窄成 JSON 对象"""
    if not isinstance(value, dict):
        raise msgspec.ValidationError(f"expected JSON object, got {type(value).__name__}")
    return cast(JsonDict, value)
