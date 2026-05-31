from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import MISSING, dataclass, fields
from typing import cast

from .._json import JsonDict, JsonValue
from ..exceptions import MaaValidationError


@dataclass
class JsonModel:
    """任务参数里的嵌套结构模型"""

    def validate(self) -> None:
        return None

    def to_json(self) -> JsonDict:
        self.validate()
        result: JsonDict = {}
        for item in fields(self):
            if item.name.startswith("_"):
                continue
            value = getattr(self, item.name)
            if value is None:
                continue
            result[item.name] = TaskBase._json_value(value, item.name)
        return result


@dataclass
class TaskBase:
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        raise NotImplementedError

    def validate(self, *, partial: bool = False) -> None:
        return None

    def to_params(self, *, validate: bool = True) -> JsonDict:
        if validate:
            self.validate(partial=False)
        return self._collect_params(skip_defaults=False)

    def to_patch(self, *, validate: bool = False) -> JsonDict:
        if validate:
            self.validate(partial=True)
        return self._collect_params(skip_defaults=True)

    def _collect_params(self, *, skip_defaults: bool) -> JsonDict:
        result: JsonDict = {}
        defaults = self._field_defaults()

        for name, value in vars(self).items():
            if name.startswith("_"):
                continue
            if value is None:
                continue
            json_value = self._json_value(value, name)
            if skip_defaults and name in defaults and json_value == defaults[name] and name != "enable":
                continue
            result[name] = json_value
        if "enable" not in result:
            result["enable"] = self.enable
        return result

    @classmethod
    def _field_defaults(cls) -> JsonDict:
        try:
            return cls.__dict__["__maapy_field_defaults__"]
        except KeyError:
            pass

        defaults: JsonDict = {}
        for item in fields(cls):
            if item.name.startswith("_"):
                continue
            if item.default is not MISSING:
                defaults[item.name] = cls._json_value(item.default, item.name)
            elif item.default_factory is not MISSING:
                factory = cast(Callable[[], object], item.default_factory)
                defaults[item.name] = cls._json_value(factory(), item.name)
        cls.__maapy_field_defaults__ = defaults
        return defaults

    @staticmethod
    def _json_value(value: object, field_name: str) -> JsonValue:
        if value is None or isinstance(value, str | bool | int):
            return value
        if isinstance(value, JsonModel):
            return value.to_json()
        if isinstance(value, float):
            if not math.isfinite(value):
                raise MaaValidationError(f"{field_name} is not a valid JSON number: {value!r}")
            return value
        if isinstance(value, list | tuple):
            return [
                TaskBase._json_value(item, f"{field_name}[{index}]")
                for index, item in enumerate(value)
            ]
        if isinstance(value, dict):
            result: JsonDict = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise MaaValidationError(f"{field_name} keys must be str: {key!r}")
                result[key] = TaskBase._json_value(item, f"{field_name}.{key}")
            return result
        raise MaaValidationError(f"{field_name} is not a valid JSON value: {value!r}")

    @staticmethod
    def _require(value: object, field_name: str) -> None:
        if value is None:
            raise MaaValidationError(f"{field_name} is required")
        if value == "":
            raise MaaValidationError(f"{field_name} cannot be empty")
        if isinstance(value, list) and not value:
            raise MaaValidationError(f"{field_name} cannot be empty")

    @staticmethod
    def _require_range(
        value: int | float,
        field_name: str,
        min_value: int | float,
        max_value: int | float,
    ) -> None:
        if not min_value <= value <= max_value:
            raise MaaValidationError(f"{field_name} must be between {min_value} and {max_value}")
