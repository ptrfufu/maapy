"""稳定回调 payload 的 msgspec.Struct 定义"""

from __future__ import annotations

import msgspec


class InitFailedPayload(msgspec.Struct):
    what: str = ""
    why: str = ""


class ConnectionDetails(msgspec.Struct):
    adb: str = ""
    address: str = ""
    config: str = ""
    uuid: str = ""
    adb_output: str = msgspec.field(default="", name="raw_output")
    width: int = 0
    height: int = 0
    reconnect: str = ""
    cmd: str = ""
    times: int = 0
    method: str = ""
    cost: int = 0
    min_cost: int = msgspec.field(default=0, name="min")
    max_cost: int = msgspec.field(default=0, name="max")
    avg_cost: int = msgspec.field(default=0, name="avg")
    fault_times: int = 0
    alternatives: list["ScreencapAlternativePayload"] = []


class ConnectionInfoPayload(msgspec.Struct):
    uuid: str = ""
    what: str = ""
    why: str = ""
    details: ConnectionDetails = msgspec.field(default_factory=ConnectionDetails)
    width: int = 0
    height: int = 0


class ScreencapAlternativePayload(msgspec.Struct):
    method: str = ""
    cost: int = 0


class AllTasksCompletedPayload(msgspec.Struct):
    uuid: str = ""
    taskchain: str = ""
    finished_tasks: list[int] = []


class AsyncCallDetails(msgspec.Struct):
    ret: bool = False
    cost: int = 0


class AsyncCallInfoPayload(msgspec.Struct):
    uuid: str = ""
    what: str = ""
    async_call_id: int = 0
    details: AsyncCallDetails = msgspec.field(default_factory=AsyncCallDetails)


class ReportRequestPayload(msgspec.Struct):
    uuid: str = ""
    url: str = ""
    headers: dict[str, str] = {}
    body: str = ""
    subtask: str = ""


class TaskChainPayload(msgspec.Struct):
    uuid: str = ""
    taskchain: str = ""
    taskid: int = 0
    what: str = ""
    why: str = ""
    node_cost: int = 0


class SubTaskPayload(msgspec.Struct):
    uuid: str = ""
    subtask: str = ""
    class_name: str = msgspec.field(default="", name="class")
    taskchain: str = ""
    taskid: int = 0
    what: str = ""
    why: str = ""


class SubTaskStartDetails(msgspec.Struct):
    task: str = ""


class ProcessTaskDetails(msgspec.Struct):
    task: str
    exec_times: int
    max_times: int
    action: str
    algorithm: str


class DropItemPayload(msgspec.Struct):
    itemId: str
    itemName: str
    quantity: int


class StageInfoPayload(msgspec.Struct):
    stageCode: str
    stageId: str


class StatItemPayload(msgspec.Struct):
    itemId: str
    itemName: str
    quantity: int
    addQuantity: int


class StageDropsDetails(msgspec.Struct):
    drops: list[DropItemPayload] = []
    stage: StageInfoPayload | None = None
    stars: int = 0
    stats: list[StatItemPayload] = []


class RecruitTagsDetectedDetails(msgspec.Struct):
    tags: list[str]


class RecruitSingleTagDetails(msgspec.Struct):
    tag: str


class RecruitResultOperPayload(msgspec.Struct):
    name: str
    id: str
    level: int


class RecruitResultOptionPayload(msgspec.Struct):
    tags: list[str]
    level: int
    opers: list[RecruitResultOperPayload]


class RecruitResultDetails(msgspec.Struct):
    tags: list[str]
    level: int
    result: list[RecruitResultOptionPayload]


class RecruitTagsRefreshedDetails(msgspec.Struct):
    count: int
    refresh_limit: int = 3


class RecruitTagsSelectedDetails(msgspec.Struct):
    tags: list[str]


class RecruitNoPermitDetails(msgspec.Struct):
    continue_refresh: bool = msgspec.field(name="continue")


class ExceededLimitDetails(msgspec.Struct):
    task: str
    exec_times: int
    max_times: int


class RecruitErrorDetails(msgspec.Struct):
    refresh_limit: int | None = None


class FacilityDetails(msgspec.Struct):
    facility: str
    index: int
    product: str | None = None


class StageNameDetails(msgspec.Struct):
    name: str


class ProductDetails(msgspec.Struct):
    product: str


class CreditFullOnlyBuyDiscountDetails(msgspec.Struct):
    credit: int


class CustomInfrastRoomGroupsMatchDetails(msgspec.Struct):
    group: str


class CustomInfrastRoomGroupsMatchFailedDetails(msgspec.Struct):
    groups: list[str]


class CustomInfrastRoomOperatorsDetails(msgspec.Struct):
    names: list[str]
    candidates: list[str]


class OperBoxOperPayload(msgspec.Struct):
    id: str
    name: str
    name_en: str = ""
    name_jp: str = ""
    name_kr: str = ""
    name_tw: str = ""
    rarity: int = 0
    own: bool = False


class OwnedOperBoxOperPayload(msgspec.Struct):
    id: str
    name: str
    own: bool = False
    elite: int = 0
    level: int = 0
    potential: int = 0
    rarity: int = 0


class OperBoxDetails(msgspec.Struct):
    done: bool
    all_opers: list[OperBoxOperPayload] = []
    own_opers: list[OwnedOperBoxOperPayload] = []


class FinishedDetails(msgspec.Struct):
    filename: str


class BattleFormationDetails(msgspec.Struct):
    formation: list[str]


class BattleFormationSelectedDetails(msgspec.Struct):
    selected: str
    group_name: str


class BattleFormationOperUnavailableDetails(msgspec.Struct):
    oper_name: str
    requirement_type: str


class AccountSwitchDetails(msgspec.Struct):
    account_name: str


class CopilotActionDetails(msgspec.Struct):
    action: str
    target: str = ""
    doc: str = ""
    doc_color: str = ""
    elapsed_time: int = 0


class CopilotListLoadTaskFileSuccessDetails(msgspec.Struct):
    stage_name: str
    file_name: str


class UserAdditionalOperInvalidDetails(msgspec.Struct):
    name: str


class InfrastTrainingCompletedDetails(msgspec.Struct):
    operator: str
    skill: str
    level: int


class InfrastTrainingTimeLeftDetails(msgspec.Struct):
    operator: str
    skill: str
    level: int
    time: str


class DepotDetails(msgspec.Struct):
    done: bool
    data: str


class SanityBeforeStageDetails(msgspec.Struct):
    report_time: str
    current_sanity: int | None = None
    max_sanity: int | None = None


class FightTimesDetails(msgspec.Struct):
    times_finished: int | None = None
    series: int | None = None
    sanity_cost: int | None = None
    finished: bool | None = None


class UseMedicineDetails(msgspec.Struct):
    is_expiring: bool
    count: int


class StageCodeDetails(msgspec.Struct):
    stage_code: str


class StageQueueMissionCompletedDetails(msgspec.Struct):
    stage_code: str
    stars: int


class UnsupportedLevelDetails(msgspec.Struct):
    level: str


class SSSStageDetails(msgspec.Struct):
    stage: str


class RoguelikeEventDetails(msgspec.Struct):
    name: str
    default_choose: int
    choose_option: int


class RoguelikeEncounterOptionPayload(msgspec.Struct):
    enabled: bool
    text: str


class RoguelikeEncounterOptionsDetails(msgspec.Struct):
    options: list[RoguelikeEncounterOptionPayload]


class BoskyPassageNodeDetails(msgspec.Struct):
    node_type: str


class RoguelikeCoppersRecognitionErrorDetails(msgspec.Struct):
    recognized_name: str


class RoguelikeCoppersExchangeInfoDetails(msgspec.Struct):
    to_discard: str
    to_pickup: str


class RoguelikeJieGardenTargetFoundDetails(msgspec.Struct):
    target_subtype: str


class FoldartalGainOcrNextLevelDetails(msgspec.Struct):
    foldartal: str


class RoguelikeCollapsalParadigmsDetails(msgspec.Struct):
    cur: str
    deepen_or_weaken: int
    prev: str


class RoguelikeInvestmentDetails(msgspec.Struct):
    count: int
    total: int
    deposit: int = -1


class RoguelikeInvestmentReachLimitDetails(msgspec.Struct):
    limit: int


class RoguelikeSettlementDetails(msgspec.Struct):
    game_pass: bool
    floor: int | None = None
    step: int | None = None
    combat: int | None = None
    recruit: int | None = None
    collection: int | None = None
    boss: int | None = None
    emergency: int | None = None
    difficulty: int | None = None
    score: int | None = None
    exp: str | None = None
    skill: str | None = None
