"""子任务消息事件 (msg 20000-20004)。

涵盖 callback-schema.md 中定义的所有 what/subtask 变体。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ._base import Event, SubTaskMixin


# ── 子任务生命周期 ──

@dataclass(slots=True, frozen=True)
class SubTaskErrorEvent(Event, SubTaskMixin):
    """msg=20000: 子任务执行/识别错误。"""
    pass


@dataclass(slots=True, frozen=True)
class SubTaskStartedEvent(Event, SubTaskMixin):
    """msg=20001: 子任务开始。"""
    task_name: str = ""


@dataclass(slots=True, frozen=True)
class SubTaskCompletedEvent(Event, SubTaskMixin):
    """msg=20002: 子任务完成。"""
    pass


@dataclass(slots=True, frozen=True)
class SubTaskStoppedEvent(Event, SubTaskMixin):
    """msg=20004: 子任务手动停止。"""
    pass


# ── SubTaskExtraInfo (msg=20003) 的 what 变体 ──

@dataclass(slots=True, frozen=True)
class ProcessTaskEvent(Event, SubTaskMixin):
    """subtask=ProcessTask: 通用流程子任务。

    details.task 常见值:
      StartButton2, MedicineConfirm, StoneConfirm,
      RecruitRefreshConfirm, RecruitConfirm, RecruitNowConfirm,
      StartExplore, 等 (见 callback-schema.md)
    """
    what: str = ""
    task_name: str = ""     # details.task
    exec_times: int = 0     # details.exec_times
    max_times: int = 0      # details.max_times
    action: int = 0         # details.action
    algorithm: int = 0      # details.algorithm


@dataclass(slots=True, frozen=True)
class StageDropsEvent(Event, SubTaskMixin):
    """what=StageDrops: 关卡材料掉落。"""
    drops: list[Any] = field(default_factory=list)       # list[DropItem]
    stage: Any = None                                     # StageInfo
    stars: int = 0
    stats: list[Any] = field(default_factory=list)        # list[StatItem]

    def get_accumulated(self, item_id: str) -> int:
        """获取某材料的累计掉落数量（跨多次作战）。"""
        for s in self.stats:
            if getattr(s, "item_id", "") == item_id:
                return getattr(s, "quantity", 0)
        return 0


@dataclass(slots=True, frozen=True)
class StageInfoEvent(Event, SubTaskMixin):
    """what=StageInfo: 作战关卡信息。"""
    name: str = ""


@dataclass(slots=True, frozen=True)
class RecruitTagsDetectedEvent(Event, SubTaskMixin):
    """what=RecruitTagsDetected / RecruitSpecialTag: 公招识别到 Tags。"""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RecruitResultEvent(Event, SubTaskMixin):
    """what=RecruitResult: 公招识别结果。"""
    tags: list[str] = field(default_factory=list)
    level: int = 0
    result: list[Any] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RecruitTagsRefreshedEvent(Event, SubTaskMixin):
    """what=RecruitTagsRefreshed: 公招刷新了 Tags。"""
    count: int = 0
    refresh_limit: int = 3


@dataclass(slots=True, frozen=True)
class RecruitTagsSelectedEvent(Event, SubTaskMixin):
    """what=RecruitTagsSelected: 公招选择了 Tags。"""
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class FacilityEvent(Event, SubTaskMixin):
    """what=EnterFacility / NotEnoughStaff / ProductOfFacility: 基建设施。"""
    what: str = ""
    facility: str = ""
    index: int = 0
    product: str | None = None


@dataclass(slots=True, frozen=True)
class OperBoxEvent(Event, SubTaskMixin):
    """what=OperBox: 干员识别结果。"""
    done: bool = False
    all_opers: list[dict] = field(default_factory=list)
    own_opers: list[dict] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class DepotEvent(Event, SubTaskMixin):
    """what=DepotInfo: 仓库识别结果（流式累加，done=true 时触发）。

    items 为 {item_id: quantity, ...} 字典。
    """
    done: bool = False
    items: dict = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class UnknownSubTaskEvent(Event, SubTaskMixin):
    """无法解析的 SubTask 消息——保留 raw dict，用户自行提取。"""
    pass
