"""MaaCore 游戏静态数据查询"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import msgspec


class ItemInfo(msgspec.Struct, frozen=True):
    """item_index.json 中的物品信息"""

    classifyType: str = ""
    description: str = ""
    icon: str = ""
    name: str = ""
    sortId: int = 0
    usage: str = ""


class CharacterInfo(msgspec.Struct, frozen=True):
    """battle_data.json 中的干员信息"""

    name: str = ""
    name_en: str = ""
    name_jp: str = ""
    name_kr: str = ""
    name_tw: str = ""
    position: str = ""
    profession: str = ""
    rangeId: list[str] = msgspec.field(default_factory=list)
    rarity: int = 0


class _BattleData(msgspec.Struct, frozen=True):
    chars: dict[str, CharacterInfo] = msgspec.field(default_factory=dict)


class GameData:
    """从 MaaCore resource 目录加载游戏静态数据"""

    def __init__(self, core_dir: str | Path):
        resource = Path(core_dir) / "resource"
        self._items = self._load_items(resource / "item_index.json")
        self._chars = self._load_battle(resource / "battle_data.json").chars

        self._name_to_id: dict[str, str] = {}
        for char_id, info in self._chars.items():
            if info.name:
                self._name_to_id[info.name] = char_id

    def item_name(self, item_id: str) -> str:
        item = self.item_info(item_id)
        return item.name if item is not None else ""

    def item_type(self, item_id: str) -> str:
        item = self.item_info(item_id)
        return item.classifyType if item is not None else ""

    def item_info(self, item_id: str) -> ItemInfo | None:
        return self._items.get(item_id)

    def all_items(self) -> dict[str, ItemInfo]:
        return self._items

    def oper_by_id(self, char_id: str) -> CharacterInfo | None:
        return self._chars.get(char_id)

    def oper_by_name(self, name: str) -> CharacterInfo | None:
        char_id = self._name_to_id.get(name)
        if char_id is None:
            return None
        return self._chars.get(char_id)

    def oper_id(self, name: str) -> str:
        return self._name_to_id.get(name, "")

    def oper_profession(self, name: str) -> str:
        info = self.oper_by_name(name)
        return info.profession if info is not None else ""

    def all_chars(self) -> dict[str, CharacterInfo]:
        return self._chars

    @staticmethod
    def _load_items(path: Path) -> dict[str, ItemInfo]:
        return msgspec.json.decode(path.read_bytes(), type=dict[str, ItemInfo])

    @staticmethod
    def _load_battle(path: Path) -> _BattleData:
        return msgspec.json.decode(path.read_bytes(), type=_BattleData)


PROFESSION_CN: Final[dict[str, str]] = {
    "CASTER": "术师",
    "MEDIC": "医疗",
    "PIONEER": "先锋",
    "SNIPER": "狙击",
    "SPECIAL": "特种",
    "SUPPORT": "辅助",
    "TANK": "重装",
    "WARRIOR": "近卫",
}

POSITION_CN: Final[dict[str, str]] = {
    "MELEE": "近战",
    "RANGED": "远程",
    "ALL": "全部",
}


__all__ = [
    "CharacterInfo",
    "GameData",
    "ItemInfo",
    "POSITION_CN",
    "PROFESSION_CN",
]
