"""MaaClient——用户面向的公开 API。
一个 MaaClient = 一台设备 = 一个 AsstHandle。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, cast

from .callback import CallbackManager
from .events._base import Event
from .events.global_events import AllTasksCompletedEvent, ConnectionEvent
from .events.subtask_events import StageDropsEvent
from .exceptions import MaaLoadError, MaaTaskError
from .instance import Instance, get_version, load_and_init, log, set_static_option


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """任务完成后的汇总结果。"""
    tag: str
    taskid: int
    status: TaskStatus
    error_message: str | None = None
    events: list[Event] = field(default_factory=list)

    @property
    def drops(self) -> list:
        """任务中所有掉落的汇总。"""
        result = []
        for e in self.events:
            if isinstance(e, StageDropsEvent):
                result.extend(e.drops)
        return result


class TaskHandle:
    """用户操作任务的主要接口。支持链式调用。"""

    def __init__(
        self,
        client: MaaClient,
        tag: str,
        taskid: int,
    ) -> None:
        self._client = client
        self._cb_mgr = client._callback_mgr
        self._instance = client._instance
        self.tag = tag
        self.taskid = taskid
        self._status = TaskStatus.PENDING
        self._result: TaskResult | None = None
        self._done = threading.Event()
        self._until_checks: list[tuple[type, Callable, threading.Event]] = []

        # 自动订阅生命周期事件以更新状态
        self._setup_auto_tracking()

    # ── 属性 ──

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def result(self) -> TaskResult | None:
        if self._result is None and self._status in (
            TaskStatus.COMPLETED,
            TaskStatus.STOPPED,
            TaskStatus.ERROR,
            TaskStatus.CANCELLED,
        ):
            self._result = TaskResult(
                tag=self.tag,
                taskid=self.taskid,
                status=self._status,
                events=self._cb_mgr.get_task_events(self.tag),
            )
        return self._result

    # ── 订阅（返回 Self 支持链式调用） ──

    def on(self, event_type: type, handler: Callable[[Event], None] | None = None) -> Any:
        """订阅此任务的特定事件。可用作装饰器: @task.on(EventType)"""
        if handler is None:
            def _decorator(fn: Callable[[Event], None]) -> Any:
                self._cb_mgr.subscribe(event_type, fn, tag=self.tag)
                return fn
            return _decorator
        self._cb_mgr.subscribe(event_type, handler, tag=self.tag)
        return self

    def until(
        self,
        event_type: type,
        predicate: Callable[[Any], bool],
    ) -> TaskHandle:
        """当 predicate(event) 为 True 时自动取消此任务。

        内部自动维护累加器（如 StageDropsEvent 的 stats 会跨回调累加）。

        Args:
            event_type: 要监听的事件类型
            predicate: 断言函数，接收事件实例，返回 True 时取消任务
        """
        def _check_and_cancel(event: Event) -> None:
            try:
                if predicate(event):
                    self.cancel()
            except Exception:
                pass

        self._cb_mgr.subscribe(event_type, _check_and_cancel, tag=self.tag)
        return self

    def stop_when(self, event_type: type):
        """装饰器版本: @task.stop_when(StageDropsEvent)"""
        def decorator(fn: Callable[[Any], bool]):
            self.until(event_type, fn)
            return fn
        return decorator

    # ── 控制 ──

    def cancel(self) -> bool:
        """取消此任务。通过设置 enable=false 实现。"""
        import json
        lib = self._instance._lib
        result = cast(Any, lib).AsstSetTaskParams(
            self._instance.handle,
            self.taskid,
            json.dumps({"enable": False}).encode("utf-8"),
        )
        if result:
            self._status = TaskStatus.CANCELLED
            self._done.set()
        return result != 0

    def set_params(self, task) -> bool:
        """运行中修改此任务的参数。"""
        from .tasks._base import TaskBase
        if isinstance(task, TaskBase):
            params = task.to_params()
        elif isinstance(task, dict):
            params = task
        else:
            raise TypeError(f"必须是 TaskBase 或 dict，收到 {type(task)}")

        import json
        lib = self._instance._lib
        return cast(Any, lib).AsstSetTaskParams(
            self._instance.handle,
            self.taskid,
            json.dumps(params, ensure_ascii=False).encode("utf-8"),
        ) != 0

    def wait(self, timeout: float | None = None) -> TaskResult | None:
        """阻塞等待此任务完成。"""
        if self._done.wait(timeout=timeout):
            return self.result
        return None

    # ── 内部 ──

    def _setup_auto_tracking(self) -> None:
        """自动订阅任务链事件以更新 TaskHandle 状态。"""
        from .events.taskchain_events import (
            TaskChainCompletedEvent,
            TaskChainErrorEvent,
            TaskChainStartEvent,
            TaskChainStoppedEvent,
        )

        def _on_start(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                self._status = TaskStatus.RUNNING

        def _on_completed(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                self._status = TaskStatus.COMPLETED
                self._done.set()

        def _on_stopped(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                self._status = TaskStatus.STOPPED
                self._done.set()

        def _on_error(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                self._status = TaskStatus.ERROR
                self._done.set()

        self._cb_mgr.subscribe(TaskChainStartEvent, _on_start, taskid=self.taskid)
        self._cb_mgr.subscribe(TaskChainCompletedEvent, _on_completed, taskid=self.taskid)
        self._cb_mgr.subscribe(TaskChainStoppedEvent, _on_stopped, taskid=self.taskid)
        self._cb_mgr.subscribe(TaskChainErrorEvent, _on_error, taskid=self.taskid)


class MaaClient:
    """MaaCore 的 Python 客户端。

    使用方式:
        MaaClient.load(core_dir="F:/maa")
        client = MaaClient()
        client.connect("127.0.0.1:5555")
        task = client.append(FightTask(stage="1-7"), tag="farm")
        client.start()
        client.wait()
    """

    # ── 静态 ──

    @staticmethod
    def load(
        core_dir: str | Path,
        user_dir: str | Path | None = None,
    ) -> str:
        """加载 MaaCore DLL 并初始化全局资源。

        Args:
            core_dir: MaaCore.dll 及 resource 目录所在路径
            user_dir: 用户数据（日志、截图）输出目录，默认 core_dir/user

        Returns:
            MaaCore 版本号字符串

        Raises:
            MaaLoadError: 加载或初始化失败
        """
        return load_and_init(str(core_dir), str(user_dir) if user_dir is not None else None)

    @staticmethod
    def loaded() -> bool:
        try:
            from .instance import _loaded
            return _loaded
        except Exception:
            return False

    @staticmethod
    def set_static_option(key: int, value: str) -> bool:
        return set_static_option(key, value)

    # ── 构造 ──

    def __init__(self) -> None:
        self._callback_mgr = CallbackManager()
        self._instance = Instance(self._callback_mgr)
        self._tasks: dict[str, TaskHandle] = {}  # tag → TaskHandle
        self._task_counter = 0

    # ── 上下文管理 ──

    def __enter__(self) -> MaaClient:
        return self

    def __exit__(self, *exc) -> None:
        self.stop()
        self._instance.destroy()

    # ── 属性 ──

    @property
    def version(self) -> str | None:
        return get_version()

    @property
    def connected(self) -> bool:
        return self._instance.connected

    @property
    def running(self) -> bool:
        return self._instance.running

    @property
    def uuid(self) -> str | None:
        u = self._instance.get_uuid()
        return u if u else None

    # ── 连接 ──

    def connect(
        self,
        address: str,
        adb_path: str | None = None,
        config: str = "General",
        timeout: float = 30.0,
    ) -> bool:
        """连接设备。

        Args:
            address: ADB 地址，如 "127.0.0.1:5555"
            adb_path: adb.exe 路径，默认使用 core_dir/adb/adb.exe
            config: 模拟器配置名，默认 "General"
            timeout: 连接超时秒数
        """
        if adb_path is None:
            # 尝试从 core_dir 推导 adb 路径
            import os
            # 从已加载的 lib 路径推导
            adb_path = "adb.exe"  # fallback

        return self._instance.connect(
            adb_path=adb_path,
            address=address,
            config=config,
            timeout=timeout,
        )

    # ── 任务 ──

    def append(self, task, *, tag: str | None = None) -> TaskHandle:
        """添加任务到队列。

        Args:
            task: TaskBase 子类实例（如 FightTask(...)）或 (type_name, params) 元组
            tag: 用户自定义标签，用于后续引用；不指定则自动生成

        Returns:
            TaskHandle——可链式调用 .on() / .until() / .wait()
        """
        from .tasks._base import TaskBase

        if isinstance(task, TaskBase):
            type_name = task.task_type()
            params = task.to_params()
        elif isinstance(task, tuple):
            type_name, params = task
        else:
            raise TypeError(f"task 必须是 TaskBase 或 (type, params) 元组，收到 {type(task)}")

        taskid = self._instance.append_task(type_name, params)

        if tag is None:
            self._task_counter += 1
            tag = f"task-{self._task_counter}"

        self._callback_mgr.register_tag(taskid, tag)

        handle = TaskHandle(self, tag, taskid)
        self._tasks[tag] = handle
        return handle

    def task(self, id_or_tag: int | str) -> TaskHandle | None:
        """按 tag 或 taskid 获取任务句柄。"""
        if isinstance(id_or_tag, str):
            return self._tasks.get(id_or_tag)
        for h in self._tasks.values():
            if h.taskid == id_or_tag:
                return h
        return None

    @property
    def tasks(self) -> list[TaskHandle]:
        return list(self._tasks.values())

    @property
    def current_task(self) -> TaskHandle | None:
        """当前正在运行的任务（通过状态判断）。"""
        for h in self._tasks.values():
            if h.status == TaskStatus.RUNNING:
                return h
        return None

    # ── 控制 ──

    def start(self) -> None:
        self._instance.start()

    def stop(self) -> None:
        self._instance.stop()

    def wait(self, timeout: float | None = None) -> bool:
        """阻塞等待所有任务完成。"""
        deadline = None if timeout is None else time.monotonic() + timeout

        # 订阅 AllTasksCompleted 事件
        done = threading.Event()

        def _on_all_done(event: Event) -> None:
            done.set()

        self._callback_mgr.subscribe(AllTasksCompletedEvent, _on_all_done)
        try:
            return done.wait(timeout=timeout)
        finally:
            self._callback_mgr.unsubscribe(AllTasksCompletedEvent, _on_all_done)

    def cancel_task(self, id_or_tag: int | str) -> bool:
        """取消指定任务。"""
        handle = self.task(id_or_tag)
        if handle is None:
            return False
        return handle.cancel()

    # ── 事件 ──

    def on(
        self, event_type: type, handler: Callable[[Event], None] | None = None,
        *, tag: str | None = None, taskid: int | None = None,
    ) -> Any:
        """订阅事件。可用作装饰器: @client.on(EventType)

        Args:
            event_type: 事件类型（如 StageDropsEvent）
            handler: 回调函数；省略时作装饰器用
            tag: 可选，仅订阅此 tag 的任务事件
            taskid: 可选，仅订阅此 taskid 的事件
        """
        if handler is None:
            def _decorator(fn: Callable[[Event], None]) -> Any:
                self._callback_mgr.subscribe(event_type, fn, tag=tag, taskid=taskid)
                return fn
            return _decorator
        self._callback_mgr.subscribe(event_type, handler, tag=tag, taskid=taskid)
        return None

    def off(self, event_type: type, handler: Callable[[Event], None]) -> None:
        self._callback_mgr.unsubscribe(event_type, handler)

    def poll_messages(self) -> list[Event]:
        return self._callback_mgr.drain()

    # ── 选项 ──

    def set_instance_option(self, key: int, value: str) -> bool:
        return self._instance.set_instance_option(key, value)

    # ── 工具 ──

    def screenshot(self) -> bytes | None:
        return self._instance.get_image_bgr()

    def click(self, x: int, y: int) -> int:
        return self._instance.click(x, y)

    def back_to_home(self) -> bool:
        return self._instance.back_to_home()

    @property
    def accumulated(self) -> dict[str, int]:
        """当前运行任务的全局累计掉落。"""
        current = self.current_task
        if current is None:
            return {}
        return dict(self._callback_mgr._accumulators.get(current.taskid, {}).get("stats", {}))

    @staticmethod
    def log(level: str, message: str) -> None:
        log(level, message)
