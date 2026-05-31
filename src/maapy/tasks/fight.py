from __future__ import annotations

from dataclasses import dataclass

from ..constants import ClientCode as ClientType, ServerCode as Server
from ._base import TaskBase


@dataclass
class FightTask(TaskBase):
    stage: str = ""
    times: int = 2147483647
    medicine: int = 0
    medicine_expire_days: int | None = None  # 与 expiring_medicine 互斥，此字段优先
    expiring_medicine: int | None = None
    stone: int = 0
    series: int = 0
    drops: dict[str, int] | None = None
    report_to_penguin: bool = False
    penguin_id: str = ""
    report_to_yituliu: bool = False
    yituliu_id: str = ""
    server: Server = "CN"
    client_type: ClientType | None = None
    DrGrandet: bool = False
    enable: bool = True

    def validate(self, *, partial: bool = False) -> None:
        super().validate(partial=partial)
        self._require_range(self.series, "series", -1, 6)

    @classmethod
    def task_type(cls) -> str:
        return "Fight"

    def to_params(self, *, validate: bool = True):
        params = super().to_params(validate=validate)
        params.pop("medicine_expire_days", None)
        if self.medicine_expire_days is not None:
            params.pop("expiring_medicine", None)
            params["medicine_expire_days"] = self.medicine_expire_days
        elif self.expiring_medicine is None:
            params.pop("expiring_medicine", None)
        return params

    def to_patch(self, *, validate: bool = False):
        params = super().to_patch(validate=validate)
        params.pop("medicine_expire_days", None)
        if self.medicine_expire_days is not None:
            params.pop("expiring_medicine", None)
            params["medicine_expire_days"] = self.medicine_expire_days
        return params
