from __future__ import annotations

from dataclasses import dataclass

from ..constants import ClientCode as ClientType, ServerCode as Server
from ._base import TaskBase


@dataclass
class FightTask(TaskBase):
    """刷理智/作战任务。

    注意: drops 参数是 MaaCore 内置支持——指定材料数量满足后自动停止。
    如需更复杂的停止条件，请使用 task.until() 绑定自定义断言。
    """

    stage: str = ""
    times: int = 2147483647
    medicine: int = 0
    expiring_medicine: int = 0
    stone: int = 0
    series: int = 0
    drops: dict[str, int] | None = None  # {"30011": 10} 刷到指定数量停止
    report_to_penguin: bool = False
    penguin_id: str = ""
    report_to_yituliu: bool = False
    yituliu_id: str = ""
    server: Server = "CN"
    client_type: ClientType | None = None
    DrGrandet: bool = False
    enable: bool = True

    @classmethod
    def task_type(cls) -> str:
        return "Fight"
