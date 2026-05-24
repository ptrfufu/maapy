"""回调管理器——C 回调 → 事件解析 → 路由分发。
线程安全：C 线程回调 → queue.Queue → Python 主线程轮询/同步分发。
"""

from __future__ import annotations

import json
import queue
from collections import defaultdict
from typing import Any, Callable

from ._ffi import ASST_API_CALLBACK_TYPE, ffi
from .constants import AsstMsg
from .events._base import (
    Event,
    SubTaskMixin,
    TaskChainMixin,
)
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


class CallbackManager:
    """管理 C 回调的生命周期、线程安全队列和事件分发。

    三级路由:
      1. msg id → 事件类
      2. what / subtask → 专用解析器
      3. 未知 → UnknownEvent (保留 raw dict)
    """

    def __init__(self) -> None:
        # 事件订阅: {EventType: [handler, ...]}
        self._listeners: dict[type, list[Callable[[Event], None]]] = defaultdict(list)
        # 按 tag 的订阅: {tag: {EventType: [handler, ...]}}
        self._tag_listeners: dict[str, dict[type, list[Callable[[Event], None]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        # 按 taskid 的订阅: {taskid: {EventType: [handler, ...]}}
        self._taskid_listeners: dict[int, dict[type, list[Callable[[Event], None]]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # taskid → tag 映射
        self._taskid_to_tag: dict[int, str] = {}

        # 消息队列 (C 线程 → 主线程)
        self._msg_queue: queue.Queue[Event] = queue.Queue()

        # tag → TaskResult 事件收集
        self._task_events: dict[str, list[Event]] = defaultdict(list)

        # 累加器: {taskid: {"stats": {item_id: quantity}, "exec_times": int}}
        self._accumulators: dict[int, dict] = defaultdict(
            lambda: {"stats": {}, "exec_times": 0, "medicine_used": 0}
        )

        # 创建 C 回调
        self._c_callback = self._make_c_callback()

    def register_tag(self, taskid: int, tag: str) -> None:
        """注册 taskid ↔ tag 映射。"""
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

    def poll(self, timeout: float = 0) -> Event | None:
        """非阻塞获取一个事件。"""
        try:
            return self._msg_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain(self) -> list[Event]:
        """获取队列中所有事件。"""
        events: list[Event] = []
        while not self._msg_queue.empty():
            try:
                events.append(self._msg_queue.get_nowait())
            except queue.Empty:
                break
        return events

    # ── C 回调属性 ──

    @property
    def c_callback(self):
        """保持引用，防止 GC 回收。"""
        return self._c_callback

    # ── 内部 ──

    def _make_c_callback(self):
        """创建 C 回调函数。在 C 线程中调用。"""

        @ffi.callback(ASST_API_CALLBACK_TYPE)
        def _cb(msg: int, details_json, custom_arg) -> None:
            try:
                raw_bytes: bytes = ffi.string(details_json)  # type: ignore[assignment]
                data = json.loads(raw_bytes.decode("utf-8")) if details_json != ffi.NULL else {}
                event = self._parse_and_route(msg, data)
                if event is None:
                    return
                self._msg_queue.put(event)
                self._dispatch(event)
            except Exception:
                # 回调内部异常绝不传播到 C 调用栈
                pass

        return _cb

    def _parse_and_route(self, msg: int, data: dict) -> Event | None:
        """一级路由：msg id → 事件解析器。"""
        msg_id = AsstMsg(msg)

        if msg_id == AsstMsg.INTERNAL_ERROR:
            return InternalErrorEvent(msg=msg_id, uuid="", raw=data)

        elif msg_id == AsstMsg.INIT_FAILED:
            return InitFailedEvent(
                msg=msg_id,
                uuid="",
                raw=data,
                what=data.get("what", ""),
                why=data.get("why", ""),
                details=data.get("details", {}),
            )

        elif msg_id == AsstMsg.CONNECTION_INFO:
            what = data.get("what", "")
            return ConnectionEvent(
                msg=msg_id,
                uuid=data.get("uuid", ""),
                raw=data,
                what=what,
                why=data.get("why", ""),
                details=data.get("details", {}),
                connected=what in ("Connected", "UuidGot"),
            )

        elif msg_id == AsstMsg.ALL_TASKS_COMPLETED:
            return AllTasksCompletedEvent(
                msg=msg_id,
                uuid=data.get("uuid", ""),
                raw=data,
                taskchain=data.get("taskchain", ""),
                finished_tasks=data.get("finished_tasks", []),
            )

        elif msg_id == AsstMsg.ASYNC_CALL_INFO:
            d = data.get("details", {})
            return AsyncCallInfoEvent(
                msg=msg_id,
                uuid=data.get("uuid", ""),
                raw=data,
                what=data.get("what", ""),
                async_call_id=data.get("async_call_id", 0),
                ret=d.get("ret", False),
                cost=d.get("cost", 0),
            )

        elif msg_id == AsstMsg.DESTROYED:
            return DestroyedEvent(msg=msg_id, uuid=data.get("uuid", ""), raw=data)

        elif msg_id in (
            AsstMsg.TASK_CHAIN_ERROR,
            AsstMsg.TASK_CHAIN_START,
            AsstMsg.TASK_CHAIN_COMPLETED,
            AsstMsg.TASK_CHAIN_EXTRA_INFO,
            AsstMsg.TASK_CHAIN_STOPPED,
        ):
            return self._parse_taskchain(msg_id, data)

        elif msg_id in (
            AsstMsg.SUB_TASK_ERROR,
            AsstMsg.SUB_TASK_START,
            AsstMsg.SUB_TASK_COMPLETED,
            AsstMsg.SUB_TASK_EXTRA_INFO,
            AsstMsg.SUB_TASK_STOPPED,
        ):
            return self._parse_subtask(msg_id, data)

        return None

    def _parse_taskchain(self, msg_id: AsstMsg, data: dict) -> Event:
        msg = int(msg_id)
        uuid: str = data.get("uuid", "")
        taskchain: str = data.get("taskchain", "")
        taskid: int = data.get("taskid", 0)

        if msg_id == AsstMsg.TASK_CHAIN_ERROR:
            return TaskChainErrorEvent(msg=msg, uuid=uuid, raw=data, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.TASK_CHAIN_START:
            return TaskChainStartEvent(msg=msg, uuid=uuid, raw=data, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.TASK_CHAIN_COMPLETED:
            return TaskChainCompletedEvent(msg=msg, uuid=uuid, raw=data, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.TASK_CHAIN_EXTRA_INFO:
            return TaskChainExtraInfoEvent(msg=msg, uuid=uuid, raw=data, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.TASK_CHAIN_STOPPED:
            return TaskChainStoppedEvent(msg=msg, uuid=uuid, raw=data, taskchain=taskchain, taskid=taskid)
        return TaskChainExtraInfoEvent(msg=msg, uuid=uuid, raw=data, taskchain=taskchain, taskid=taskid)

    def _parse_subtask(self, msg_id: AsstMsg, data: dict) -> Event:
        msg = int(msg_id)
        uuid: str = data.get("uuid", "")
        subtask: str = data.get("subtask", "")
        class_name: str = data.get("class", "")
        taskchain: str = data.get("taskchain", "")
        taskid: int = data.get("taskid", 0)

        if msg_id == AsstMsg.SUB_TASK_ERROR:
            return SubTaskErrorEvent(msg=msg, uuid=uuid, raw=data, subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.SUB_TASK_START:
            d = data.get("details", {})
            return SubTaskStartedEvent(msg=msg, uuid=uuid, raw=data, subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid, task_name=d.get("task", ""))
        elif msg_id == AsstMsg.SUB_TASK_COMPLETED:
            return SubTaskCompletedEvent(msg=msg, uuid=uuid, raw=data, subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.SUB_TASK_STOPPED:
            return SubTaskStoppedEvent(msg=msg, uuid=uuid, raw=data, subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid)
        elif msg_id == AsstMsg.SUB_TASK_EXTRA_INFO:
            return self._parse_subtask_extra(data, msg=msg, uuid=uuid, subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid)

        return UnknownSubTaskEvent(msg=msg, uuid=uuid, raw=data, subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid)

    def _parse_subtask_extra(
        self, data: dict, *,
        msg: int, uuid: str, subtask: str, class_name: str, taskchain: str, taskid: int,
    ) -> Event:
        """二级路由：SubTaskExtraInfo 按 what 字段解析。"""
        what = data.get("what", "")
        sub_details = data.get("details", {})

        if data.get("subtask") == "ProcessTask":
            return ProcessTaskEvent(
                msg=msg, uuid=uuid, raw=data,
                taskchain=taskchain, taskid=taskid,
                what=what,
                task_name=sub_details.get("task", ""),
                exec_times=sub_details.get("exec_times", 0),
                max_times=sub_details.get("max_times", 0),
            )

        if what == "StageDrops":
            drops_raw = sub_details.get("drops", [])
            stage_raw = sub_details.get("stage", {})
            stats_raw = sub_details.get("stats", [])
            return StageDropsEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                drops=[DropItem(**d) for d in drops_raw],
                stage=StageInfo(**stage_raw) if stage_raw else StageInfo(),
                stars=sub_details.get("stars", 0),
                stats=[StatItem(**s) for s in stats_raw],
            )
        elif what == "RecruitTagsDetected":
            return RecruitTagsDetectedEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                tags=sub_details.get("tags", []),
            )
        elif what == "RecruitSpecialTag":
            return RecruitTagsDetectedEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                tags=[sub_details.get("tag", "")],
            )
        elif what == "RecruitResult":
            result_raw = sub_details.get("result", [])
            return RecruitResultEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                tags=sub_details.get("tags", []),
                level=sub_details.get("level", 0),
                result=[RecruitOption(**r) for r in result_raw],
            )
        elif what == "RecruitTagsRefreshed":
            return RecruitTagsRefreshedEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                count=sub_details.get("count", 0),
                refresh_limit=sub_details.get("refresh_limit", 3),
            )
        elif what == "RecruitTagsSelected":
            return RecruitTagsSelectedEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                tags=sub_details.get("tags", []),
            )
        elif what in ("EnterFacility", "NotEnoughStaff", "ProductOfFacility"):
            return FacilityEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                what=what,
                facility=sub_details.get("facility", ""),
                index=sub_details.get("index", 0),
                product=sub_details.get("product") if what == "ProductOfFacility" else None,
            )
        elif what == "StageInfo":
            return StageInfoEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
                name=sub_details.get("name", ""),
            )
        elif what == "Depot":
            return UnknownSubTaskEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
            )
        elif what == "OperBox":
            return UnknownSubTaskEvent(
                msg=msg, uuid=uuid, raw=data,
                subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
            )

        return UnknownSubTaskEvent(
            msg=msg, uuid=uuid, raw=data,
            subtask=subtask, class_name=class_name, taskchain=taskchain, taskid=taskid,
        )

    # ── 事件分发 ──

    def _dispatch(self, event: Event) -> None:
        """在 C 线程中同步调用监听器。用户需自行处理线程安全。"""
        taskid = getattr(event, "taskid", None)

        # 收集事件到 TaskResult
        if taskid:
            tag = self._taskid_to_tag.get(taskid)
            if tag:
                self._task_events[tag].append(event)

        # 累加 stats
        if isinstance(event, StageDropsEvent):
            acc = self._accumulators[event.taskid]
            for s in event.stats:
                acc["stats"][s.item_id] = max(
                    acc["stats"].get(s.item_id, 0), s.quantity
                )

        # 分发: 按 Event 类型
        for handler in self._listeners.get(type(event), []):
            self._safe_call(handler, event)
        for handler in self._listeners.get(Event, []):
            self._safe_call(handler, event)

        # 分发: 按 tag
        if taskid:
            tag = self._taskid_to_tag.get(taskid)
            if tag and tag in self._tag_listeners:
                for handler in self._tag_listeners[tag].get(type(event), []):
                    self._safe_call(handler, event)

        # 分发: 按 taskid
        if taskid and taskid in self._taskid_listeners:
            for handler in self._taskid_listeners[taskid].get(type(event), []):
                self._safe_call(handler, event)

    def _safe_call(self, handler, event: Event) -> None:
        try:
            handler(event)
        except Exception:
            pass  # 不破坏分发链

    # ── 便捷查询 ──

    def get_task_events(self, tag: str) -> list[Event]:
        """获取某 tag 对应的所有已收集事件。"""
        return self._task_events.get(tag, [])

    def get_accumulated(self, taskid: int, item_id: str) -> int:
        """获取某任务的累计材料数量。"""
        return self._accumulators[taskid]["stats"].get(item_id, 0)


# ── 事件子类型（小 dataclass，供 StageDropsEvent 等使用） ──

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class DropItem:
    item_id: str = ""
    item_name: str = ""
    quantity: int = 0

    def __init__(self, itemId: str = "", itemName: str = "", quantity: int = 0):
        # 使用 object.__setattr__ 绕过 frozen
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
