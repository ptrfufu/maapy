from __future__ import annotations

from typing import ClassVar, Literal, TypeAlias

import msgspec

from ._json import JsonDict
from .constants import ClientCode


ConnectionConfigName: TypeAlias = Literal["MuMuEmulator12", "LDPlayer"]


class MuMuConnectionExtras(msgspec.Struct, frozen=True):
    """MuMu 12 截图增强连接参数"""

    path: str
    index: int | None = None
    client_type: ClientCode | None = None

    config_name: ClassVar[Literal["MuMuEmulator12"]] = "MuMuEmulator12"

    def to_json(self) -> JsonDict:
        result: JsonDict = {"path": self.path}
        if self.index is not None:
            result["index"] = self.index
        if self.client_type is not None:
            result["client_type"] = self.client_type
        return result


class LDPlayerConnectionExtras(msgspec.Struct, frozen=True):
    """雷电模拟器截图增强连接参数"""

    path: str
    index: int | None = None
    pid: int | None = None

    config_name: ClassVar[Literal["LDPlayer"]] = "LDPlayer"

    def to_json(self) -> JsonDict:
        result: JsonDict = {"path": self.path}
        if self.index is not None:
            result["index"] = self.index
        if self.pid is not None:
            result["pid"] = self.pid
        return result


ConnectionExtras: TypeAlias = MuMuConnectionExtras | LDPlayerConnectionExtras
