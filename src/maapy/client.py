"""MaaClient——用户面向的公开 API。
一个 MaaClient = 一台设备 = 一个 AsstHandle。
"""

from __future__ import annotations

import inspect
import threading
from dataclasses import dataclass, field
from time import time as _time
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, TypeAlias, cast

if TYPE_CHECKING:
    from pathlib import Path
    from .tasks._base import TaskBase

from ._json import JsonDict
from .callback import CallbackManager, Subscription
from .connection import ConnectionExtras
from .events._base import Event
from .events.global_events import AllTasksCompletedEvent, CallbackErrorEvent
from .events.rules import (
    Action,
    AppendTask,
    CancelAndAppend,
    CancelTask,
    ChangedSpec,
    Continue,
    EventContext,
    EventRule,
    StopCore,
    UpdateParams,
    WhenSpec,
)
from .events.subtask_events import StageDropsEvent
from .instance import Instance, get_core_dir, get_version, load_and_init, log, set_static_option
from .exceptions import MaaTaskError, MaaValidationError


EventHandler: TypeAlias = Callable[..., object]


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
        self._error_message: str | None = None
        self._started_at: float | None = None
        self._finished_at: float | None = None
        self._result: TaskResult | None = None
        self._done = threading.Event()
        self._subscriptions: list[Subscription] = []

        # 自动订阅生命周期事件以更新状态
        self._setup_auto_tracking()

    def __repr__(self) -> str:
        return f"TaskHandle(tag={self.tag!r}, taskid={self.taskid}, status={self._status.value})"

    # ── 属性 ──

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def done(self) -> bool:
        """任务是否已结束（完成/停止/错误/取消）。"""
        return self._status in (
            TaskStatus.COMPLETED,
            TaskStatus.STOPPED,
            TaskStatus.ERROR,
            TaskStatus.CANCELLED,
        )

    @property
    def started_at(self) -> float | None:
        """任务开始运行的时间戳（epoch 秒），未开始时为 None。"""
        return self._started_at

    @property
    def finished_at(self) -> float | None:
        """任务结束的时间戳（epoch 秒），未结束时为 None。"""
        return self._finished_at

    @property
    def elapsed(self) -> float | None:
        """任务已运行秒数（进行中）或总耗时（已结束），未开始时为 None。"""
        if self._started_at is None:
            return None
        end = self._finished_at if self._finished_at is not None else _time()
        return end - self._started_at

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
                error_message=self._error_message,
                events=self._cb_mgr.get_task_events(self.tag),
            )
        return self._result

    # ── 订阅（返回 Self 支持链式调用） ──

    def on(
        self,
        event_type: type,
        handler: EventHandler | None = None,
        *,
        changed: ChangedSpec = None,
        when: WhenSpec = None,
        block: bool = False,
    ) -> Any:
        """订阅此任务的特定事件。可用作装饰器: @task.on(EventType)"""
        if handler is None:
            def _decorator(fn: EventHandler) -> Any:
                sub = self._client._subscribe_event(
                    event_type,
                    fn,
                    tag=self.tag,
                    task=self,
                    changed=changed,
                    when=when,
                    block=block,
                    track_off=False,
                )
                self._subscriptions.append(sub)
                fn._maapy_subscription = sub  # type: ignore[attr-defined]
                return fn
            return _decorator
        self._subscriptions.append(
            self._client._subscribe_event(
                event_type,
                handler,
                tag=self.tag,
                task=self,
                changed=changed,
                when=when,
                block=block,
                track_off=False,
            )
        )
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
            except Exception as exc:
                from .events.global_events import CallbackErrorEvent
                self._cb_mgr._dispatch(CallbackErrorEvent(
                    msg=event.msg,
                    uuid=event.uuid,
                    source="until",
                    error=f"{type(exc).__name__}: {exc}",
                ))

        self._subscriptions.append(
            self._cb_mgr.subscribe(event_type, _check_and_cancel, tag=self.tag)
        )
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
        result = self._instance.set_task_params(self.taskid, {"enable": False})
        if result:
            self._finish(TaskStatus.CANCELLED)
        return result

    def set_params(self, task: TaskBase) -> bool:
        """运行中修改此任务的参数。"""
        from .tasks._base import TaskBase
        if isinstance(task, TaskBase):
            return self._instance.set_task_params(self.taskid, task.to_patch())
        raise TypeError(f"必须是 TaskBase，收到 {type(task)}")

    def wait(self, timeout: float | None = None) -> TaskResult | None:
        """阻塞等待此任务完成，超时返回 None。"""
        if self._done.wait(timeout=timeout):
            return self.result
        return None

    def wait_or_raise(self, timeout: float | None = None) -> TaskResult:
        """阻塞等待此任务完成，超时抛出 TimeoutError。"""
        if self._done.wait(timeout=timeout):
            result = self.result
            assert result is not None
            return result
        raise TimeoutError(
            f"任务 {self.tag!r} (id={self.taskid}) 在 {timeout}s 内未完成，当前状态: {self._status.value}"
        )

    async def wait_async(self, timeout: float | None = None) -> TaskResult | None:
        """异步等待此任务完成（不阻塞事件循环）。"""
        import asyncio
        return await asyncio.get_running_loop().run_in_executor(None, self.wait, timeout)

    def stream(self, event_type: type):
        """流式生成器，逐次 yields 指定类型的事件直至任务结束。

        Usage:
            for event in task.stream(OperBoxEvent):
                print(f"进度: {len(event.own_opers)} 干员")
                if event.done:
                    print("识别完成!")
        """
        import queue

        if self._status in (TaskStatus.COMPLETED, TaskStatus.ERROR, TaskStatus.STOPPED, TaskStatus.CANCELLED):
            return

        q: queue.Queue[Event | None] = queue.Queue()

        def _handler(e: Event) -> None:
            q.put(e)

        def _on_stop(e: Event) -> None:
            if getattr(e, "taskid", 0) == self.taskid:
                q.put(None)  # sentinel

        from .events.taskchain_events import (
            TaskChainCompletedEvent,
            TaskChainErrorEvent,
            TaskChainStoppedEvent,
        )
        from .events.subtask_events import SubTaskCompletedEvent, SubTaskErrorEvent

        self._cb_mgr.subscribe(event_type, _handler, tag=self.tag)
        self._cb_mgr.subscribe(SubTaskCompletedEvent, _on_stop, taskid=self.taskid)
        self._cb_mgr.subscribe(SubTaskErrorEvent, _on_stop, taskid=self.taskid)
        self._cb_mgr.subscribe(TaskChainCompletedEvent, _on_stop, taskid=self.taskid)
        self._cb_mgr.subscribe(TaskChainErrorEvent, _on_stop, taskid=self.taskid)
        self._cb_mgr.subscribe(TaskChainStoppedEvent, _on_stop, taskid=self.taskid)

        try:
            while True:
                event = q.get()
                if event is None:
                    break
                yield event
        finally:
            self._cb_mgr.unsubscribe(event_type, _handler)
            self._cb_mgr.unsubscribe(SubTaskCompletedEvent, _on_stop)
            self._cb_mgr.unsubscribe(SubTaskErrorEvent, _on_stop)
            self._cb_mgr.unsubscribe(TaskChainCompletedEvent, _on_stop)
            self._cb_mgr.unsubscribe(TaskChainErrorEvent, _on_stop)
            self._cb_mgr.unsubscribe(TaskChainStoppedEvent, _on_stop)

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
                self._started_at = _time()

        def _on_completed(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                self._finish(TaskStatus.COMPLETED)

        def _on_stopped(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                self._finish(TaskStatus.STOPPED)

        def _on_error(event: Event) -> None:
            if getattr(event, "taskid", 0) == self.taskid:
                why = getattr(event, "why", "") or ""
                self._finish(TaskStatus.ERROR, error_message=why if why else None)

        self._subscriptions.extend([
            self._cb_mgr.subscribe(TaskChainStartEvent, _on_start, taskid=self.taskid),
            self._cb_mgr.subscribe(TaskChainCompletedEvent, _on_completed, taskid=self.taskid),
            self._cb_mgr.subscribe(TaskChainStoppedEvent, _on_stopped, taskid=self.taskid),
            self._cb_mgr.subscribe(TaskChainErrorEvent, _on_error, taskid=self.taskid),
        ])

    def _finish(self, status: TaskStatus, error_message: str | None = None) -> None:
        self._status = status
        self._finished_at = _time()
        self._error_message = error_message
        self._done.set()
        self._dispose_subscriptions()

    def _dispose_subscriptions(self) -> None:
        subscriptions, self._subscriptions = self._subscriptions, []
        for subscription in subscriptions:
            subscription.close()


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
        from .instance import _loaded
        return _loaded

    @staticmethod
    def set_static_option(key: int, value: str) -> bool:
        return set_static_option(key, value)

    # ── 构造 ──

    def __init__(self) -> None:
        self._callback_mgr = CallbackManager()
        self._instance = Instance(self._callback_mgr)
        self._tasks: dict[str, TaskHandle] = {}  # tag → TaskHandle
        self._taskid_to_handle: dict[int, TaskHandle] = {}
        self._event_wrappers: dict[tuple[type, EventHandler], list[Callable[[Event], None]]] = {}
        self._task_counter = 0

    # ── 上下文管理 ──

    def __enter__(self) -> MaaClient:
        return self

    def __exit__(self, *exc) -> None:
        try:
            self.stop()
        finally:
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
        extras: ConnectionExtras | None = None,
    ) -> bool:
        """连接设备。

        Args:
            address: ADB 地址，如 "127.0.0.1:5555"
            adb_path: adb.exe 路径，默认使用 core_dir/adb/adb.exe
            config: 模拟器配置名，默认 "General"
            timeout: 连接超时秒数
            extras: MuMu / LDPlayer 截图增强参数
        """
        config = self._resolve_connection_config(config, extras)
        if extras is not None:
            self._instance.set_connection_extras(extras)

        if adb_path is None:
            core_dir = get_core_dir()
            if core_dir is None:
                raise RuntimeError("MaaCore 未加载，无法推导 adb_path")
            import sys
            adb_name = "adb.exe" if sys.platform == "win32" else "adb"
            adb_path = str(core_dir / "adb" / adb_name)

        return self._instance.connect(
            adb_path=adb_path,
            address=address,
            config=config,
            timeout=timeout,
        )

    def set_connection_extras(self, extras: ConnectionExtras) -> None:
        self._instance.set_connection_extras(extras)

    @staticmethod
    def _resolve_connection_config(config: str, extras: ConnectionExtras | None) -> str:
        if extras is None:
            return config
        if config == "General":
            return extras.config_name
        if config != extras.config_name:
            raise MaaValidationError(
                f"连接增强参数 {extras.config_name!r} 不能用于连接配置 {config!r}"
            )
        return config

    def attach_window(
        self,
        hwnd: int,
        screencap_method: int,
        mouse_method: int,
        keyboard_method: int,
    ) -> bool:
        """同步绑定 Win32 窗口，参数值见 Win32ScreencapMethod / Win32InputMethod。"""
        return self._instance.attach_window(
            hwnd=hwnd,
            screencap_method=screencap_method,
            mouse_method=mouse_method,
            keyboard_method=keyboard_method,
        )

    def async_attach_window(
        self,
        hwnd: int,
        screencap_method: int,
        mouse_method: int,
        keyboard_method: int,
        *,
        block: bool = False,
    ) -> int:
        """异步绑定 Win32 窗口，返回 MaaCore 异步调用 ID。"""
        return self._instance.async_attach_window(
            hwnd=hwnd,
            screencap_method=screencap_method,
            mouse_method=mouse_method,
            keyboard_method=keyboard_method,
            block=block,
        )

    # ── 任务 ──

    def append(self, task: TaskBase, *, tag: str | None = None) -> TaskHandle:
        """添加任务到队列。

        Args:
            task: TaskBase 子类实例（如 FightTask(...)）
            tag: 用户自定义标签，用于后续引用；不指定则自动生成

        Returns:
            TaskHandle——可链式调用 .on() / .until() / .wait()
        """
        from .tasks._base import TaskBase

        if isinstance(task, TaskBase):
            type_name = task.task_type()
            params = task.to_params()
        else:
            raise TypeError(f"task 必须是 TaskBase，收到 {type(task)}")

        return self._append_prepared(type_name, params, tag=tag)

    def _append_prepared(self, type_name: str, params: JsonDict, *, tag: str | None = None) -> TaskHandle:
        taskid = self._instance.append_task(type_name, params)

        if tag is None:
            self._task_counter += 1
            tag = f"task-{self._task_counter}"

        self._callback_mgr.register_tag(taskid, tag)

        handle = TaskHandle(self, tag, taskid)
        self._tasks[tag] = handle
        self._taskid_to_handle[taskid] = handle
        return handle

    def task(self, id_or_tag: int | str) -> TaskHandle | None:
        """按 tag 或 taskid 获取任务句柄。"""
        if isinstance(id_or_tag, str):
            return self._tasks.get(id_or_tag)
        return self._taskid_to_handle.get(id_or_tag)

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
        done = threading.Event()

        def _on_all_done(_event: Event) -> None:
            done.set()

        self._callback_mgr.subscribe(AllTasksCompletedEvent, _on_all_done)
        try:
            return done.wait(timeout=timeout)
        finally:
            self._callback_mgr.unsubscribe(AllTasksCompletedEvent, _on_all_done)

    async def wait_async(self, timeout: float | None = None) -> bool:
        """异步等待所有任务完成（不阻塞事件循环）。"""
        import asyncio
        return await asyncio.get_running_loop().run_in_executor(None, self.wait, timeout)

    def cancel_task(self, id_or_tag: int | str) -> bool:
        """取消指定任务。"""
        handle = self.task(id_or_tag)
        if handle is None:
            return False
        return handle.cancel()

    # ── 事件 ──

    def on(
        self,
        event_type: type,
        handler: EventHandler | None = None,
        *,
        tag: str | None = None,
        taskid: int | None = None,
        changed: ChangedSpec = None,
        when: WhenSpec = None,
        block: bool = False,
    ) -> Any:
        """订阅事件。可用作装饰器: @client.on(EventType)

        Args:
            event_type: 事件类型（如 StageDropsEvent）
            handler: 回调函数；省略时作装饰器用
            tag: 可选，仅订阅此 tag 的任务事件
            taskid: 可选，仅订阅此 taskid 的事件
        """
        if handler is None:
            def _decorator(fn: EventHandler) -> Any:
                sub = self._subscribe_event(
                    event_type,
                    fn,
                    tag=tag,
                    taskid=taskid,
                    changed=changed,
                    when=when,
                    block=block,
                )
                fn._maapy_subscription = sub  # type: ignore[attr-defined]
                return fn
            return _decorator
        self._subscribe_event(
            event_type,
            handler,
            tag=tag,
            taskid=taskid,
            changed=changed,
            when=when,
            block=block,
        )
        return None

    def off(self, event_type: type, handler: EventHandler) -> None:
        wrappers = self._event_wrappers.pop((event_type, handler), [])
        for wrapper in wrappers:
            self._callback_mgr.unsubscribe(event_type, wrapper)
        self._callback_mgr.unsubscribe(event_type, cast(Callable[[Event], None], handler))

    def poll_messages(self) -> list[Event]:
        return self._callback_mgr.archived_events()

    def _subscribe_event(
        self,
        event_type: type,
        handler: EventHandler,
        *,
        tag: str | None = None,
        taskid: int | None = None,
        task: TaskHandle | None = None,
        changed: ChangedSpec = None,
        when: WhenSpec = None,
        block: bool = False,
        track_off: bool = True,
    ) -> Subscription:
        rule = EventRule.build(changed=changed, when=when)
        wrapped = self._wrap_event_handler(handler, rule, block=block, task=task)
        if track_off:
            self._event_wrappers.setdefault((event_type, handler), []).append(wrapped)
        return self._callback_mgr.subscribe(event_type, wrapped, tag=tag, taskid=taskid)

    def _wrap_event_handler(
        self,
        handler: EventHandler,
        rule: EventRule,
        *,
        block: bool,
        task: TaskHandle | None,
    ) -> Callable[[Event], None]:
        def _wrapped(event: Event) -> None:
            try:
                match = rule.match(event)
                if match is None:
                    return
                ctx = EventContext(
                    event=event,
                    client=self,
                    task=task or self._task_from_event(event),
                    match=match,
                )
                result = self._call_event_handler(handler, event, ctx)
                if block:
                    self._apply_action(result, ctx)
            except Exception as exc:
                self._emit_callback_error(event, "event_rule", exc)

        return _wrapped

    @staticmethod
    def _call_event_handler(handler: EventHandler, event: Event, ctx: EventContext) -> object:
        signature = inspect.signature(handler)
        parameters = list(signature.parameters.values())
        if "ctx" in signature.parameters:
            return handler(event, ctx=ctx)
        positional = [
            parameter
            for parameter in parameters
            if parameter.kind in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        has_varargs = any(
            parameter.kind == inspect.Parameter.VAR_POSITIONAL
            for parameter in parameters
        )
        if has_varargs or len(positional) >= 2:
            return handler(event, ctx)
        return handler(event)

    def _apply_action(self, action: object, ctx: EventContext) -> None:
        if action is None or isinstance(action, Continue):
            return
        if isinstance(action, StopCore):
            self.stop()
            return
        if isinstance(action, CancelTask):
            self._require_action_task(action, ctx).cancel()
            return
        if isinstance(action, UpdateParams):
            target = self._require_action_task(action, ctx)
            target.set_params(action.params)
            return
        if isinstance(action, AppendTask):
            self.append(action.task, tag=action.tag)
            if action.start:
                self.start()
            return
        if isinstance(action, CancelAndAppend):
            self._require_current_action_task(ctx).cancel()
            self.append(action.task, tag=action.tag)
            if action.start:
                self.start()
            return
        raise TypeError(f"block=True 的事件处理器必须返回 Action 或 None，收到 {type(action).__name__}")

    def _require_action_task(
        self,
        action: CancelTask | UpdateParams,
        ctx: EventContext,
    ) -> TaskHandle:
        task: TaskHandle | None = None
        if action.tag is not None:
            task = self.task(action.tag)
        elif action.taskid is not None:
            task = self.task(action.taskid)
        elif ctx.task is not None:
            task = ctx.task
        else:
            task = self._task_from_event(ctx.event)
        if task is None:
            raise MaaTaskError("事件动作无法定位目标任务")
        return task

    def _require_current_action_task(self, ctx: EventContext) -> TaskHandle:
        task = ctx.task or self._task_from_event(ctx.event)
        if task is None:
            raise MaaTaskError("事件动作无法定位当前任务")
        return task

    def _task_from_event(self, event: Event) -> TaskHandle | None:
        taskid = getattr(event, "taskid", None)
        if isinstance(taskid, int):
            return self.task(taskid)
        return None

    def _emit_callback_error(self, event: Event, source: str, exc: BaseException) -> None:
        self._callback_mgr._dispatch(CallbackErrorEvent(
            msg=event.msg,
            uuid=event.uuid,
            source=source,
            error=f"{type(exc).__name__}: {exc}",
        ))

    # ── 选项 ──

    def set_instance_option(self, key: int, value: str) -> bool:
        return self._instance.set_instance_option(key, value)

    # ── 工具 ──

    def screenshot(self) -> bytes:
        return self._instance.get_image_bgr()

    def screenshot_to_file(self, path: str | Path) -> int:
        """截图并保存为 PNG，返回写入的字节数。"""
        from pathlib import Path as _Path
        data = self._instance.get_image()
        _Path(path).write_bytes(data)
        return len(data)

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
        return self._callback_mgr.get_all_accumulated(current.taskid)

    @staticmethod
    def log(level: str, message: str) -> None:
        log(level, message)
