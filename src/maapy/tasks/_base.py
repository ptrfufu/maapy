"""任务基类。"""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field
from typing import Any


@dataclass
class TaskBase:
    """所有任务类型的基类。

    子类需重写 task_type() 返回 AsstTaskType 字符串。
    enable 和 _extra 是所有任务共有的字段。
    """
    enable: bool = True
    _extra: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def task_type(cls) -> str:
        """返回 AsstAppendTask 的 type 参数值。子类必须覆盖。"""
        raise NotImplementedError

    def to_params(self) -> dict[str, Any]:
        """序列化为 MaaCore JSON。排除 None、_前缀字段、以及值为默认值的字段。"""
        result: dict[str, Any] = {}
        defaults: dict[str, Any] = self._get_field_defaults()

        for name, value in vars(self).items():
            if name.startswith("_"):
                continue
            if value is None:
                continue
            if name in defaults and value == defaults[name] and name != "enable":
                continue
            result[name] = value
        result.update(self._extra)
        if "enable" not in result:
            result["enable"] = self.enable
        return result

    def _get_field_defaults(self) -> dict[str, Any]:
        """获取字段默认值，首次调用时计算并缓存到类上。"""
        cls = type(self)
        try:
            return cls._field_defaults
        except AttributeError:
            pass
        defaults: dict[str, Any] = {}
        for f in cls.__dataclass_fields__.values():
            if not f.name.startswith("_"):
                if f.default is not MISSING:
                    defaults[f.name] = f.default
                elif f.default_factory is not MISSING:
                    defaults[f.name] = f.default_factory()
        cls._field_defaults = defaults
        return defaults
