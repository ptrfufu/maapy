"""事件装饰器规则 DSL。"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeAlias, TypeVar, cast

from ._base import Event

if TYPE_CHECKING:
    from ..client import MaaClient, TaskHandle
    from ..tasks._base import TaskBase


T = TypeVar("T")
PathPart: TypeAlias = str | int


class FieldResolveError(LookupError):
    """字段路径解析失败。"""


class _Missing:
    pass


MISSING = _Missing()


class LogicMode(Enum):
    ANY = "any"
    ALL = "all"


@dataclass(slots=True, frozen=True)
class LogicToken:
    mode: LogicMode


@dataclass(slots=True, frozen=True, eq=False)
class FieldExpr(Generic[T]):
    """事件字段表达式，E.foo.bar 表示 event.foo.bar。"""

    path: tuple[PathPart, ...] = ()
    modifiers: frozenset[str] = frozenset()

    def __getattr__(self, name: str) -> Any:
        if name == "_initial":
            return self._with_modifier("initial")
        if name == "_strict":
            return self._with_modifier("strict")
        if not self.path and name == "_any":
            return LogicToken(LogicMode.ANY)
        if not self.path and name == "_all":
            return LogicToken(LogicMode.ALL)
        if name.startswith("_"):
            raise AttributeError(f"未知事件虚字段: {name}")
        return FieldExpr[Any](self.path + (name,), self.modifiers)

    def __getitem__(self, key: str | int) -> FieldExpr[Any]:
        return FieldExpr[Any](self.path + (key,), self.modifiers)

    def __eq__(self, expected: object) -> Any:
        return FieldCondition(self, expected)

    def in_(self, expected: Iterable[T]) -> FieldCondition:
        return FieldCondition(self, list(expected))

    def where(self, predicate: Callable[[T], bool]) -> PredicateCondition:
        return PredicateCondition(self, cast(Callable[[object], bool], predicate))

    def __hash__(self) -> int:
        return hash((self.path, self.modifiers))

    def _with_modifier(self, modifier: str) -> FieldExpr[T]:
        return FieldExpr(self.path, self.modifiers | {modifier})

    @property
    def strict(self) -> bool:
        return "strict" in self.modifiers

    @property
    def initial(self) -> bool:
        return "initial" in self.modifiers

    @property
    def key(self) -> tuple[PathPart, ...]:
        return self.path

    @property
    def label(self) -> str:
        return ".".join(str(part) for part in self.path)


@dataclass(slots=True, frozen=True)
class FieldCondition:
    field: FieldExpr[Any]
    expected: object

    def matches(self, event: Event) -> bool:
        value = resolve_field(event, self.field)
        if value is MISSING:
            return False
        if _is_membership_expected(self.expected, value):
            return value in cast(Iterable[object], self.expected)
        return value == self.expected


@dataclass(slots=True, frozen=True)
class PredicateCondition:
    field: FieldExpr[Any]
    predicate: Callable[[object], bool]

    def matches(self, event: Event) -> bool:
        value = resolve_field(event, self.field)
        if value is MISSING:
            return False
        return self.predicate(value)


ChangedSpec: TypeAlias = (
    FieldExpr[Any] | LogicToken | Sequence[FieldExpr[Any] | LogicToken] | None
)
ConditionSpec: TypeAlias = FieldCondition | PredicateCondition
WhenSpec: TypeAlias = (
    ConditionSpec | LogicToken | Sequence[ConditionSpec | LogicToken] | None
)


@dataclass(slots=True, frozen=True)
class FieldChange:
    field: FieldExpr[Any]
    value: object
    previous: object
    initial: bool


@dataclass(slots=True, frozen=True)
class EventMatch:
    changes: dict[str, FieldChange] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class EventContext:
    event: Event
    client: MaaClient
    task: TaskHandle | None
    match: EventMatch

    @property
    def changes(self) -> dict[str, FieldChange]:
        return self.match.changes


@dataclass(slots=True)
class EventRule:
    """事件匹配规则，支持 changed（字段变化检测）和 when（条件断言）。

    注意：EventRule 是有状态的——它内部追踪每个字段的"上次值"以检测变化。
    请勿跨事件流或跨 MaaClient 复用同一个 EventRule 实例。
    如需重置状态，调用 reset()。
    """

    changed_fields: list[FieldExpr[Any]]
    changed_logic: LogicMode
    conditions: list[ConditionSpec]
    when_logic: LogicMode
    _seen: set[tuple[PathPart, ...]] = field(default_factory=set)
    _previous: dict[tuple[PathPart, ...], object] = field(default_factory=dict)

    def reset(self) -> None:
        """重置内部追踪状态，可安全复用于新的事件流。"""
        self._seen.clear()
        self._previous.clear()

    @classmethod
    def build(cls, changed: ChangedSpec = None, when: WhenSpec = None) -> EventRule:
        changed_logic, changed_fields = _normalize_changed(changed)
        when_logic, conditions = _normalize_when(when)
        return cls(
            changed_fields=changed_fields,
            changed_logic=changed_logic,
            conditions=conditions,
            when_logic=when_logic,
        )

    def match(self, event: Event) -> EventMatch | None:
        changes = self._match_changed(event)
        if changes is None:
            return None
        if not self._match_when(event):
            return None
        return EventMatch(changes=changes)

    def _match_changed(self, event: Event) -> dict[str, FieldChange] | None:
        if not self.changed_fields:
            return {}

        results: list[FieldChange | None] = []
        for field_expr in self.changed_fields:
            results.append(self._field_change(event, field_expr))

        if self.changed_logic == LogicMode.ALL and any(
            change is None for change in results
        ):
            return None
        if self.changed_logic == LogicMode.ANY and all(
            change is None for change in results
        ):
            return None

        return {change.field.label: change for change in results if change is not None}

    def _field_change(
        self, event: Event, field_expr: FieldExpr[Any]
    ) -> FieldChange | None:
        value = resolve_field(event, field_expr)
        if value is MISSING:
            return None

        key = field_expr.key
        snapshot = _snapshot(value)
        if key not in self._seen:
            self._seen.add(key)
            self._previous[key] = snapshot
            if field_expr.initial:
                return FieldChange(field_expr, value, MISSING, initial=True)
            return None

        previous = self._previous[key]
        self._previous[key] = snapshot
        if value == previous:
            return None
        return FieldChange(field_expr, value, previous, initial=False)

    def _match_when(self, event: Event) -> bool:
        if not self.conditions:
            return True

        results = [condition.matches(event) for condition in self.conditions]
        if self.when_logic == LogicMode.ALL:
            return all(results)
        return any(results)


@dataclass(slots=True, frozen=True)
class Continue:
    """继续当前 Python 事件分发，不对 MaaCore 做动作。"""


@dataclass(slots=True, frozen=True)
class StopCore:
    """停止 MaaCore 当前实例。"""


@dataclass(slots=True, frozen=True)
class CancelTask:
    """取消当前任务或指定任务。"""

    taskid: int | None = None
    tag: str | None = None


@dataclass(slots=True, frozen=True)
class AppendTask:
    """追加一个新任务。start=True 时会尝试启动 MaaCore。"""

    task: TaskBase
    tag: str | None = None
    start: bool = False


@dataclass(slots=True, frozen=True)
class CancelAndAppend:
    """取消当前任务后追加新任务，这是 Python 层编排，不是 Core 内部跳转。"""

    task: TaskBase
    tag: str | None = None
    start: bool = False


@dataclass(slots=True, frozen=True)
class UpdateParams:
    """修改当前任务或指定任务参数。"""

    params: TaskBase
    taskid: int | None = None
    tag: str | None = None


Action: TypeAlias = (
    Continue | StopCore | CancelTask | AppendTask | CancelAndAppend | UpdateParams
)

E: FieldExpr[Any] = FieldExpr()


def resolve_field(event: Event, field_expr: FieldExpr[Any]) -> object:
    current: object = event
    for part in field_expr.path:
        try:
            current = _resolve_part(current, part)
        except (AttributeError, KeyError, IndexError, TypeError) as exc:
            if field_expr.strict:
                raise FieldResolveError(
                    f"事件字段不存在或类型不匹配: {field_expr.label}"
                ) from exc
            return MISSING
    return current


def _resolve_part(current: object, part: PathPart) -> object:
    if isinstance(part, int):
        if not isinstance(current, Sequence) or isinstance(
            current, str | bytes | bytearray
        ):
            raise TypeError(part)
        return current[part]

    if isinstance(current, dict):
        return current[part]
    return getattr(current, part)


def _normalize_changed(spec: ChangedSpec) -> tuple[LogicMode, list[FieldExpr[Any]]]:
    logic = LogicMode.ANY
    fields: list[FieldExpr[Any]] = []
    for item in _as_items(spec):
        if isinstance(item, LogicToken):
            logic = item.mode
        elif isinstance(item, FieldExpr):
            _require_path(item)
            fields.append(item)
        else:
            raise TypeError(f"changed 只支持事件字段表达式，收到 {type(item).__name__}")
    return logic, fields


def _normalize_when(spec: WhenSpec) -> tuple[LogicMode, list[ConditionSpec]]:
    logic = LogicMode.ALL
    conditions: list[ConditionSpec] = []
    for item in _as_items(spec):
        if isinstance(item, LogicToken):
            logic = item.mode
        elif isinstance(item, FieldCondition | PredicateCondition):
            _require_path(item.field)
            conditions.append(item)
        else:
            raise TypeError(f"when 只支持字段条件表达式，收到 {type(item).__name__}")
    return logic, conditions


def _as_items(spec: object) -> list[object]:
    if spec is None:
        return []
    if isinstance(spec, list | tuple):
        return list(spec)
    return [spec]


def _require_path(field_expr: FieldExpr[Any]) -> None:
    if not field_expr.path:
        raise ValueError("事件字段表达式不能为空")


def _is_membership_expected(expected: object, value: object) -> bool:
    if isinstance(expected, str | bytes | bytearray | dict):
        return False
    if isinstance(value, list | tuple | set | frozenset):
        return False
    return isinstance(expected, Iterable)


def _snapshot(value: object) -> object:
    if isinstance(value, list | dict | set):
        return copy.deepcopy(value)
    return value
