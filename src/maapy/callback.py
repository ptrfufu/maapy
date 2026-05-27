"""回调管理器——C 回调 → 事件解析 → 路由分发。

C 线程回调只做解析 + 入队；后台 daemon 线程持续 drain 并 dispatch，
确保用户事件处理器在 Python 线程中执行，不阻塞 MaaCore C++ 工作线程。
"""

from __future__ import annotations

import json
import logging
import queue
import threading
from collections import defaultdict
from typing import Callable

from ._ffi import ASST_API_CALLBACK_TYPE, ffi
from .constants import AsstMsg
from .events._base import Event
from .events.global_events import (
    AllTasksCompletedEvent,
    AsyncCallInfoEvent,
    ConnectionEvent,
    DestroyedEvent,
    InitFailedEvent,
    InternalErrorEvent,
)
from .events.subtask_events import (
    FacilityEvent,
    OperBoxEvent,
    ProcessTaskEvent,
    RecruitResultEvent,
    RecruitTagsDetectedEvent,
    RecruitTagsRefreshedEvent,
    RecruitTagsSelectedEvent,
    StageDropsEvent,
    StageInfoEvent,
    SubTaskCompletedEvent,
    SubTaskErrorEvent,
    SubTaskStartedEvent,
    SubTaskStoppedEvent,
    UnknownSubTaskEvent,
)
from .events.taskchain_events import (
    TaskChainCompletedEvent,
    TaskChainErrorEvent,
    TaskChainExtraInfoEvent,
    TaskChainStartEvent,
    TaskChainStoppedEvent,
)

_logger = logging.getLogger(__name__)

_MAX_TASK_EVENTS = 10000


class CallbackManager:
    """管理 C 回调的生命周期、线程安全队列和事件分发。

    三级路由:
      1. msg id → 事件类
      2. what / subtask → 专用解析器
      3. 未知 → UnknownEvent (保留 raw dict)

    C 回调只负责解析 + 入队；后台 daemon 线程持续 dispatch。
    """

    def __init__(self) -> None:
        self._listeners: dict[type, list[Callable[[Event], None]]] = defaultdict(list)
        self._tag_listeners: dict[str, dict[type, list[Callable[[Event], None]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._taskid_listeners: dict[int, dict[type, list[Callable[[Event], None]]]] = defaultdict(
            lambda: defaultdict(list)
        )

        self._taskid_to_tag: dict[int, str] = {}

        self._msg_queue: queue.Queue[Event] = queue.Queue()

        self._task_events: dict[str, list[Event]] = defaultdict(list)

        self._accumulators: dict[int, dict] = defaultdict(
            lambda: {"stats": {}, "exec_times": 0, "medicine_used": 0}
        )

        self._lock = threading.Lock()
        self._shutdown = threading.Event()

        # 启动 daemon 线程持续分发事件
        self._dispatch_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True, name="maapy-dispatch"
        )
        self._dispatch_thread.start()

        self._msg_dispatch: dict[AsstMsg, Callable] = {
            AsstMsg.INTERNAL_ERROR:       self._parse_internal_error,
            AsstMsg.INIT_FAILED:          self._parse_init_failed,
            AsstMsg.CONNECTION_INFO:      self._parse_connection_info,
            AsstMsg.ALL_TASKS_COMPLETED:  self._parse_all_tasks_completed,
            AsstMsg.ASYNC_CALL_INFO:      self._parse_async_call_info,
            AsstMsg.DESTROYED:            self._parse_destroyed,
            AsstMsg.TASK_CHAIN_ERROR:     self._parse_taskchain,
            AsstMsg.TASK_CHAIN_START:     self._parse_taskchain,
            AsstMsg.TASK_CHAIN_COMPLETED: self._parse_taskchain,
            AsstMsg.TASK_CHAIN_EXTRA_INFO: self._parse_taskchain,
            AsstMsg.TASK_CHAIN_STOPPED:   self._parse_taskchain,
            AsstMsg.SUB_TASK_ERROR:       self._parse_subtask,
            AsstMsg.SUB_TASK_START:       self._parse_subtask,
            AsstMsg.SUB_TASK_COMPLETED:   self._parse_subtask,
            AsstMsg.SUB_TASK_EXTRA_INFO:  self._parse_subtask,
            AsstMsg.SUB_TASK_STOPPED:     self._parse_subtask,
        }

        self._subtask_extra_parsers: dict[str, Callable] = {
            "StageDrops":             self._parse_stage_drops,
            "RecruitTagsDetected":    self._parse_recruit_tags_detected,
            "RecruitSpecialTag":      self._parse_recruit_special_tag,
            "RecruitResult":          self._parse_recruit_result,
            "RecruitTagsRefreshed":   self._parse_recruit_tags_refreshed,
            "RecruitTagsSelected":    self._parse_recruit_tags_selected,
            "EnterFacility":          self._parse_facility,
            "NotEnoughStaff":         self._parse_facility,
            "ProductOfFacility":      self._parse_facility,
            "StageInfo":              self._parse_stage_info,
            "OperBox":                self._parse_operbox,
        }

        self._taskchain_event_classes: dict[AsstMsg, type] = {
            AsstMsg.TASK_CHAIN_ERROR:       TaskChainErrorEvent,
            AsstMsg.TASK_CHAIN_START:       TaskChainStartEvent,
            AsstMsg.TASK_CHAIN_COMPLETED:   TaskChainCompletedEvent,
            AsstMsg.TASK_CHAIN_EXTRA_INFO:  TaskChainExtraInfoEvent,
            AsstMsg.TASK_CHAIN_STOPPED:     TaskChainStoppedEvent,
        }

        self._subtask_event_classes: dict[AsstMsg, type] = {
            AsstMsg.SUB_TASK_ERROR:      SubTaskErrorEvent,
            AsstMsg.SUB_TASK_START:      SubTaskStartedEvent,
            AsstMsg.SUB_TASK_COMPLETED:  SubTaskCompletedEvent,
            AsstMsg.SUB_TASK_STOPPED:    SubTaskStoppedEvent,
        }

        self._c_callback = self._make_c_callback()

    def register_tag(self, taskid: int, tag: str) -> None:
        self._taskid_to_tag[taskid] = tag

    # ── 订阅管理 ──

    def subscribe(
        self,
        event_type: type,
        handler: Callable[[Event], None],
        *,
        taskid: int | None = None,
        tag: str | None = None,
    ) -> None:
        if taskid is not None:
            self._taskid_listeners[taskid][event_type].append(handler)
        elif tag is not None:
            self._tag_listeners[tag][event_type].append(handler)
        else:
            self._listeners[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: Callable[[Event], None]) -> None:
        if handler in self._listeners.get(event_type, []):
            self._listeners[event_type].remove(handler)
        for tag_handlers in self._tag_listeners.values():
            if handler in tag_handlers.get(event_type, []):
                tag_handlers[event_type].remove(handler)
        for tid_handlers in self._taskid_listeners.values():
            if handler in tid_handlers.get(event_type, []):
                tid_handlers[event_type].remove(handler)

    # ── 消息队列 ──

    def _dispatch_loop(self) -> None:
        """Daemon 线程：持续 drain 队列并 dispatch 事件。"""
        while not self._shutdown.is_set():
            try:
                event = self._msg_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            except Exception:
                continue
            try:
                self._dispatch(event)
            except Exception:
                _logger.debug("Dispatch loop error", exc_info=True)

    def poll(self, timeout: float = 0) -> Event | None:
        """获取并分发一个事件（daemon 之外兜底）。"""
        try:
            event = self._msg_queue.get(timeout=timeout)
        except queue.Empty:
            return None
        self._dispatch(event)
        return event

    def drain(self) -> list[Event]:
        """获取并分发队列中所有事件（daemon 之外兜底）。"""
        events: list[Event] = []
        while not self._msg_queue.empty():
            try:
                events.append(self._msg_queue.get_nowait())
            except queue.Empty:
                break
        for event in events:
            self._dispatch(event)
        return events

    # ── C 回调属性 ──

    @property
    def c_callback(self):
        return self._c_callback

    # ── C 回调 ──

    def _make_c_callback(self):
        """创建 C 回调——运行在 C++ 工作线程，只做解析 + 入队。"""

        @ffi.callback(ASST_API_CALLBACK_TYPE)
        def _cb(msg: int, details_json, custom_arg) -> None:
            try:
                raw_bytes: bytes = ffi.string(details_json)  # type: ignore[assignment]
                data = json.loads(raw_bytes.decode("utf-8")) if details_json != ffi.NULL else {}
                event = self._parse_and_route(msg, data)
                if event is not None:
                    self._msg_queue.put(event)
            except Exception:
                _logger.debug("C callback parse error", exc_info=True)

        return _cb

    # ── 一级路由 — dict dispatch ──

    def _parse_and_route(self, msg: int, data: dict) -> Event | None:
        msg_id = AsstMsg(msg)
        parser = self._msg_dispatch.get(msg_id)
        if parser is not None:
            return parser(msg_id, data)
        return None

    # ── 全局事件解析器 ──

    def _parse_internal_error(self, msg_id: AsstMsg, data: dict) -> Event:
        return InternalErrorEvent(msg=int(msg_id), uuid="", raw=data)

    def _parse_init_failed(self, msg_id: AsstMsg, data: dict) -> Event:
        return InitFailedEvent(
            msg=int(msg_id), uuid="", raw=data,
            what=data.get("what", ""),
            why=data.get("why", ""),
            details=data.get("details", {}),
        )

    def _parse_connection_info(self, msg_id: AsstMsg, data: dict) -> Event:
        what = data.get("what", "")
        return ConnectionEvent(
            msg=int(msg_id), uuid=data.get("uuid", ""), raw=data,
            what=what, why=data.get("why", ""),
            details=data.get("details", {}),
            connected=what in ("Connected", "UuidGot"),
        )

    def _parse_all_tasks_completed(self, msg_id: AsstMsg, data: dict) -> Event:
        return AllTasksCompletedEvent(
            msg=int(msg_id), uuid=data.get("uuid", ""), raw=data,
            taskchain=data.get("taskchain", ""),
            finished_tasks=data.get("finished_tasks", []),
        )

    def _parse_async_call_info(self, msg_id: AsstMsg, data: dict) -> Event:
        d = data.get("details", {})
        return AsyncCallInfoEvent(
            msg=int(msg_id), uuid=data.get("uuid", ""), raw=data,
            what=data.get("what", ""),
            async_call_id=data.get("async_call_id", 0),
            ret=d.get("ret", False),
            cost=d.get("cost", 0),
        )

    def _parse_destroyed(self, msg_id: AsstMsg, data: dict) -> Event:
        return DestroyedEvent(msg=int(msg_id), uuid=data.get("uuid", ""), raw=data)

    # ── TaskChain / SubTask 解析 ──

    def _parse_taskchain(self, msg_id: AsstMsg, data: dict) -> Event:
        cls = self._taskchain_event_classes.get(msg_id, TaskChainExtraInfoEvent)
        return cls(
            msg=int(msg_id), uuid=data.get("uuid", ""), raw=data,
            taskchain=data.get("taskchain", ""), taskid=data.get("taskid", 0),
        )

    def _parse_subtask(self, msg_id: AsstMsg, data: dict) -> Event:
        msg = int(msg_id)
        uuid: str = data.get("uuid", "")
        subtask: str = data.get("subtask", "")
        class_name: str = data.get("class", "")
        taskchain: str = data.get("taskchain", "")
        taskid: int = data.get("taskid", 0)

        if msg_id == AsstMsg.SUB_TASK_EXTRA_INFO:
            return self._parse_subtask_extra(
                data, msg=msg, uuid=uuid, subtask=subtask,
                class_name=class_name, taskchain=taskchain, taskid=taskid,
            )

        cls = self._subtask_event_classes.get(msg_id)
        if cls is None:
            return UnknownSubTaskEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name,
                taskchain=taskchain, taskid=taskid,
            )

        if msg_id == AsstMsg.SUB_TASK_START:
            d = data.get("details", {})
            return cls(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name,
                taskchain=taskchain, taskid=taskid,
                task_name=d.get("task", ""),
            )
        return cls(
            msg=msg, uuid=uuid, raw=data,
            subtask=subtask, class_name=class_name,
            taskchain=taskchain, taskid=taskid,
        )

    def _parse_subtask_extra(
        self, data: dict, *,
        msg: int, uuid: str, subtask: str, class_name: str, taskchain: str, taskid: int,
    ) -> Event:
        if data.get("subtask") == "ProcessTask":
            return self._parse_process_task(
                data, msg=msg, uuid=uuid, taskchain=taskchain, taskid=taskid,
            )

        what = data.get("what", "")
        parser = self._subtask_extra_parsers.get(what)
        if parser is not None:
            return parser(data, msg=msg, uuid=uuid, subtask=subtask,
                          class_name=class_name, taskchain=taskchain, taskid=taskid)

        return UnknownSubTaskEvent(
            msg=msg, uuid=uuid, raw=data,
            subtask=subtask, class_name=class_name,
            taskchain=taskchain, taskid=taskid,
        )

    def _parse_process_task(
        self, data: dict, *,
        msg: int, uuid: str, taskchain: str, taskid: int,
    ) -> Event:
        sub_details = data.get("details", {})
        return ProcessTaskEvent(
            msg=msg, uuid=uuid, raw=data,
            subtask=data.get("subtask", ""),
            class_name=data.get("class", ""),
            taskchain=taskchain, taskid=taskid,
            what=data.get("what", ""),
            task_name=sub_details.get("task", ""),
            exec_times=sub_details.get("exec_times", 0),
            max_times=sub_details.get("max_times", 0),
        )

    def _parse_stage_drops(
        self, data: dict, **kwargs,
    ) -> Event:
        sub_details = data.get("details", {})
        drops_raw = sub_details.get("drops", [])
        stage_raw = sub_details.get("stage", {})
        stats_raw = sub_details.get("stats", [])
        return StageDropsEvent(
            **kwargs,
            drops=[DropItem(**d) for d in drops_raw],
            stage=StageInfo(**stage_raw) if stage_raw else StageInfo(),
            stars=sub_details.get("stars", 0),
            stats=[StatItem(**s) for s in stats_raw],
        )

    def _parse_recruit_tags_detected(self, data: dict, **kwargs) -> Event:
        return RecruitTagsDetectedEvent(
            **kwargs,
            tags=data.get("details", {}).get("tags", []),
        )

    def _parse_recruit_special_tag(self, data: dict, **kwargs) -> Event:
        return RecruitTagsDetectedEvent(
            **kwargs,
            tags=[data.get("details", {}).get("tag", "")],
        )

    def _parse_recruit_result(self, data: dict, **kwargs) -> Event:
        sub_details = data.get("details", {})
        return RecruitResultEvent(
            **kwargs,
            tags=sub_details.get("tags", []),
            level=sub_details.get("level", 0),
            result=[RecruitOption(**r) for r in sub_details.get("result", [])],
        )

    def _parse_recruit_tags_refreshed(self, data: dict, **kwargs) -> Event:
        sub_details = data.get("details", {})
        return RecruitTagsRefreshedEvent(
            **kwargs,
            count=sub_details.get("count", 0),
            refresh_limit=sub_details.get("refresh_limit", 3),
        )

    def _parse_recruit_tags_selected(self, data: dict, **kwargs) -> Event:
        return RecruitTagsSelectedEvent(
            **kwargs,
            tags=data.get("details", {}).get("tags", []),
        )

    def _parse_facility(self, data: dict, **kwargs) -> Event:
        sub_details = data.get("details", {})
        what = data.get("what", "")
        return FacilityEvent(
            **kwargs,
            what=what,
            facility=sub_details.get("facility", ""),
            index=sub_details.get("index", 0),
            product=sub_details.get("product") if what == "ProductOfFacility" else None,
        )

    def _parse_stage_info(self, data: dict, **kwargs) -> Event:
        return StageInfoEvent(
            **kwargs,
            name=data.get("details", {}).get("name", ""),
        )

    def _parse_operbox(self, data: dict, **kwargs) -> Event:
        sub_details = data.get("details", {})
        return OperBoxEvent(
            **kwargs,
            done=sub_details.get("done", False),
            all_opers=sub_details.get("all_opers", []),
            own_opers=sub_details.get("own_opers", []),
        )

    # ── 事件分发 ──

    def _dispatch(self, event: Event) -> None:
        """分发事件到所有匹配的订阅者。调用者需保证非 C 线程。"""
        taskid = getattr(event, "taskid", None)

        with self._lock:
            if taskid:
                tag = self._taskid_to_tag.get(taskid)
                if tag:
                    events = self._task_events[tag]
                    if len(events) < _MAX_TASK_EVENTS:
                        events.append(event)

            if isinstance(event, StageDropsEvent):
                acc = self._accumulators[event.taskid]
                for s in event.stats:
                    acc["stats"][s.item_id] = max(
                        acc["stats"].get(s.item_id, 0), s.quantity
                    )

        for handler in self._listeners.get(type(event), []):
            self._safe_call(handler, event)
        for handler in self._listeners.get(Event, []):
            self._safe_call(handler, event)

        if taskid:
            tag = self._taskid_to_tag.get(taskid)
            if tag and tag in self._tag_listeners:
                for handler in self._tag_listeners[tag].get(type(event), []):
                    self._safe_call(handler, event)

        if taskid and taskid in self._taskid_listeners:
            for handler in self._taskid_listeners[taskid].get(type(event), []):
                self._safe_call(handler, event)

    def _safe_call(self, handler, event: Event) -> None:
        try:
            handler(event)
        except Exception:
            _logger.debug("Event handler error", exc_info=True)

    # ── 便捷查询 ──

    def get_task_events(self, tag: str) -> list[Event]:
        with self._lock:
            return list(self._task_events.get(tag, []))

    def get_accumulated(self, taskid: int, item_id: str) -> int:
        with self._lock:
            return self._accumulators[taskid]["stats"].get(item_id, 0)


# ── 事件子类型 ──

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class DropItem:
    item_id: str = ""
    item_name: str = ""
    quantity: int = 0

    def __init__(self, itemId: str = "", itemName: str = "", quantity: int = 0):
        object.__setattr__(self, "item_id", itemId)
        object.__setattr__(self, "item_name", itemName)
        object.__setattr__(self, "quantity", quantity)


@dataclass(slots=True, frozen=True)
class StageInfo:
    stage_code: str = ""
    stage_id: str = ""

    def __init__(self, stageCode: str = "", stageId: str = ""):
        object.__setattr__(self, "stage_code", stageCode)
        object.__setattr__(self, "stage_id", stageId)


@dataclass(slots=True, frozen=True)
class StatItem:
    item_id: str = ""
    item_name: str = ""
    quantity: int = 0
    add_quantity: int = 0

    def __init__(self, itemId: str = "", itemName: str = "", quantity: int = 0, addQuantity: int = 0):
        object.__setattr__(self, "item_id", itemId)
        object.__setattr__(self, "item_name", itemName)
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "add_quantity", addQuantity)


@dataclass(slots=True, frozen=True)
class RecruitOption:
    tags: list[str] = field(default_factory=list)
    level: int = 0
    opers: list[dict] = field(default_factory=list)
