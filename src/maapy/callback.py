"""回调管理器，负责把 MaaCore 回调解析为强类型事件并完成线程安全分发"""

from __future__ import annotations

import logging
import queue
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from typing import Callable

from ._callback.parser import CallbackParser
from ._ffi import ASST_API_CALLBACK_TYPE, ffi
from ._json import JsonDict, decode_json_dict
from .constants import AsstMsg
from .events._base import Event
from .events.global_events import CallbackErrorEvent
from .events.subtask_events import StageDropsEvent

_logger = logging.getLogger(__name__)

_MAX_TASK_EVENTS = 10000


class _StopEvent:
    pass


_STOP_EVENT = _StopEvent()


@dataclass(frozen=True)
class Subscription:
    """可释放的订阅句柄，避免任务结束后监听器常驻"""

    manager: "CallbackManager"
    event_type: type
    handler: Callable[[Event], None]

    def close(self) -> None:
        self.manager.unsubscribe(self.event_type, self.handler)


@dataclass(slots=True)
class _TaskAccumulator:
    """任务级聚合态——跨回调累加的业务数据（目前仅用于掉落统计）。"""

    stats: dict[str, int] = field(default_factory=dict)


class CallbackManager:
    """管理 C 回调的生命周期、解析过程和事件分发。

    使用 CallbackParser 组合（非 mixin 继承）处理 JSON 解析。
    """

    @staticmethod
    def _on_callback_error(event: Event) -> None:
        _logger.error("maapy 事件处理器异常 [%s]: %s", getattr(event, "source", "?"), getattr(event, "error", "?"))

    def __init__(self) -> None:
        self._parser = CallbackParser()

        self._listeners: dict[type, list[Callable[[Event], None]]] = defaultdict(list)
        self._tag_listeners: dict[str, dict[type, list[Callable[[Event], None]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._taskid_listeners: dict[int, dict[type, list[Callable[[Event], None]]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # handler → {(event_type, tag_or_None, taskid_or_None), ...} 反向索引
        self._handler_registry: dict[int, set[tuple[type, str | None, int | None]]] = defaultdict(set)

        self._taskid_to_tag: dict[int, str] = {}
        self._msg_queue: queue.Queue[Event | _StopEvent] = queue.Queue()
        self._task_events: dict[str, list[Event]] = defaultdict(list)
        self._event_archive: list[Event] = []
        self._closed = False

        self._accumulators: dict[int, _TaskAccumulator] = defaultdict(_TaskAccumulator)

        self._lock = threading.Lock()
        self._shutdown = threading.Event()

        self._dispatch_thread = threading.Thread(
            target=self._dispatch_loop,
            daemon=True,
            name="maapy-dispatch",
        )
        self._dispatch_thread.start()

        self._c_callback = self._make_c_callback()

        # 默认监听 CallbackErrorEvent，确保 handler 异常总是可见
        self.subscribe(CallbackErrorEvent, self._on_callback_error)

    # ── 公开方法 ──

    def register_tag(self, taskid: int, tag: str) -> None:
        self._taskid_to_tag[taskid] = tag

    def close(self, timeout: float = 1.0) -> None:
        """关闭后台分发线程并释放所有订阅"""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._shutdown.set()
            self._listeners.clear()
            self._tag_listeners.clear()
            self._taskid_listeners.clear()
            self._handler_registry.clear()
        self._msg_queue.put(_STOP_EVENT)
        self._dispatch_thread.join(timeout=timeout)

    def subscribe(
        self,
        event_type: type,
        handler: Callable[[Event], None],
        *,
        taskid: int | None = None,
        tag: str | None = None,
    ) -> Subscription:
        with self._lock:
            if taskid is not None:
                self._taskid_listeners[taskid][event_type].append(handler)
            elif tag is not None:
                self._tag_listeners[tag][event_type].append(handler)
            else:
                self._listeners[event_type].append(handler)
            self._handler_registry[id(handler)].add((event_type, tag, taskid))
        return Subscription(self, event_type, handler)

    def unsubscribe(self, event_type: type, handler: Callable[[Event], None]) -> None:
        """通过反向索引 O(1) 定位并移除 handler。"""
        handler_id = id(handler)
        with self._lock:
            registrations = self._handler_registry.pop(handler_id, set())
            for ev_type, tag, taskid in registrations:
                if ev_type is not event_type:
                    # 同一个 handler 可能被注册到不同 event_type（通过 off() 的 wrapper）
                    # 这里只移除匹配 event_type 的注册
                    self._handler_registry[handler_id].add((ev_type, tag, taskid))
                    continue
                if taskid is not None:
                    lst = self._taskid_listeners.get(taskid, {}).get(ev_type)
                elif tag is not None:
                    lst = self._tag_listeners.get(tag, {}).get(ev_type)
                else:
                    lst = self._listeners.get(ev_type)
                if lst is not None and handler in lst:
                    lst.remove(handler)

    def archived_events(self) -> list[Event]:
        """返回已分发事件快照，避免和后台线程竞争同一个队列"""
        with self._lock:
            return list(self._event_archive)

    @property
    def c_callback(self):
        return self._c_callback

    def get_task_events(self, tag: str) -> list[Event]:
        with self._lock:
            return list(self._task_events.get(tag, []))

    def get_accumulated(self, taskid: int, item_id: str) -> int:
        with self._lock:
            return self._accumulators[taskid].stats.get(item_id, 0)

    def get_all_accumulated(self, taskid: int) -> dict[str, int]:
        """返回指定任务的全部累计掉落统计快照。"""
        with self._lock:
            acc = self._accumulators.get(taskid)
            if acc is None:
                return {}
            return dict(acc.stats)

    # ── 委托给 CallbackParser 的解析方法（供测试使用） ──

    def _parse_subtask(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        return self._parser._parse_subtask(msg_id, data)

    def _parse_taskchain(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        return self._parser._parse_taskchain(msg_id, data)

    def _parse_report_request(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        return self._parser._parse_report_request(msg_id, data)

    def _parse_connection_info(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        return self._parser._parse_connection_info(msg_id, data)

    def _parse_async_call_info(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        return self._parser._parse_async_call_info(msg_id, data)

    # ── 内部 ──

    def _make_c_callback(self):
        """创建 C 回调，C++ 线程只负责解码和入队"""

        @ffi.callback(ASST_API_CALLBACK_TYPE)
        def _cb(msg: int, details_json, custom_arg) -> None:
            del custom_arg
            try:
                if details_json == ffi.NULL:
                    data: JsonDict = {}
                else:
                    payload_bytes = ffi.string(details_json)
                    data = decode_json_dict(payload_bytes)
                event = self._parser.parse_and_route(msg, data)
                if event is not None:
                    self._msg_queue.put(event)
            except Exception as exc:
                _logger.warning("C callback parse error: %s", exc)
                self._msg_queue.put(self._parser.make_callback_error(msg, "parse", exc))

        return _cb

    def _dispatch_loop(self) -> None:
        """后台线程持续 drain 队列并分发事件"""
        while not self._shutdown.is_set():
            try:
                event = self._msg_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            except Exception:
                _logger.exception("Dispatch queue error")
                continue
            if isinstance(event, _StopEvent):
                break
            try:
                self._dispatch(event)
            except Exception:
                _logger.exception("Dispatch loop error")

    def _dispatch(self, event: Event) -> None:
        """把事件发给所有匹配的订阅者，且支持父类订阅命中子类事件"""
        taskid = getattr(event, "taskid", None)

        with self._lock:
            self._event_archive.append(event)
            if taskid:
                tag = self._taskid_to_tag.get(taskid)
                if tag:
                    tagged_events = self._task_events[tag]
                    if len(tagged_events) < _MAX_TASK_EVENTS:
                        tagged_events.append(event)

            if isinstance(event, StageDropsEvent):
                accumulator = self._accumulators[event.taskid]
                for stat in event.stats:
                    accumulator.stats[stat.item_id] = max(
                        accumulator.stats.get(stat.item_id, 0),
                        stat.quantity,
                    )

            # 沿 MRO 向上派发，订阅基类时也能接住具体子类事件
            dispatch_types = self._mro_dispatch_types(type(event))

            listeners: list[Callable[[Event], None]] = []
            for event_type in dispatch_types:
                listeners.extend(self._listeners.get(event_type, []))

            tag_handlers: list[Callable[[Event], None]] = []
            if taskid:
                tag = self._taskid_to_tag.get(taskid)
                if tag and tag in self._tag_listeners:
                    for event_type in dispatch_types:
                        tag_handlers.extend(self._tag_listeners[tag].get(event_type, []))

            taskid_handlers: list[Callable[[Event], None]] = []
            if taskid and taskid in self._taskid_listeners:
                for event_type in dispatch_types:
                    taskid_handlers.extend(self._taskid_listeners[taskid].get(event_type, []))

        seen_handlers: set[int] = set()
        for handler in chain(listeners, tag_handlers, taskid_handlers):
            marker = id(handler)
            if marker in seen_handlers:
                continue
            seen_handlers.add(marker)
            self._safe_call(handler, event)

    def _mro_dispatch_types(self, event_type: type) -> list[type]:
        """缓存 MRO 中 Event 子类的列表，避免每次分发都重新计算。"""
        cache = getattr(self, "_mro_cache", None)
        if cache is None:
            cache = {}
            self._mro_cache = cache
        if event_type in cache:
            return cache[event_type]
        result = [
            cls
            for cls in event_type.__mro__
            if cls is not object and issubclass(cls, Event)
        ]
        cache[event_type] = result
        return result

    def _safe_call(self, handler: Callable[[Event], None], event: Event) -> None:
        try:
            handler(event)
        except Exception as exc:
            _logger.exception("Event handler error")
            error = CallbackErrorEvent(
                msg=event.msg,
                uuid=event.uuid,
                source="handler",
                error=f"{type(exc).__name__}: {exc}",
            )
            with self._lock:
                self._event_archive.append(error)
