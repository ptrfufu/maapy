"""回调解析器——所有解析逻辑集中在一个平坦类中（不使用 mixin 继承）。"""

from __future__ import annotations

from typing import Unpack

import msgspec

from .._json import JsonDict
from ..constants import AsstMsg, AsyncCallWhat, ConnectionWhat, SubTaskWhat
from ..events._base import Event
from ..events.global_events import (
    AllTasksCompletedEvent,
    AttachWindowAsyncCallInfoEvent,
    CallbackErrorEvent,
    ClickAsyncCallInfoEvent,
    ConnectAsyncCallInfoEvent,
    ConnectFailedConnectionEvent,
    ConnectedConnectionEvent,
    DestroyedEvent,
    DisconnectConnectionEvent,
    FastestWayToScreencapConnectionEvent,
    InitFailedEvent,
    InternalErrorEvent,
    ReconnectedConnectionEvent,
    ReconnectingConnectionEvent,
    ReportRequestEvent,
    ResolutionErrorConnectionEvent,
    ResolutionGotConnectionEvent,
    ResolutionInfoConnectionEvent,
    ScreencapAsyncCallInfoEvent,
    ScreencapCostConnectionEvent,
    ScreencapFailedConnectionEvent,
    ScreencapMethodAlternative,
    TouchModeNotAvailableConnectionEvent,
    UnknownAsyncCallInfoEvent,
    UnsupportedPlayToolsConnectionEvent,
    UnsupportedResolutionConnectionEvent,
    UuidGotConnectionEvent,
)
from ..events.subtask_events import (
    AccountSwitchEvent,
    BattleFormationEvent,
    BattleFormationOperUnavailableEvent,
    BattleFormationParseFailedEvent,
    BattleFormationSelectedEvent,
    BoskyPassageNodeEvent,
    ClassifyDirectionCompletedEvent,
    ClassifyDirectionErrorEvent,
    ClassifyDirectionStartedEvent,
    CompSkillCompletedEvent,
    CompSkillErrorEvent,
    CompSkillStartedEvent,
    CopilotActionEvent,
    CopilotListLoadTaskFileSuccessEvent,
    CreditFullOnlyBuyDiscountEvent,
    CustomInfrastRoomGroupsMatchEvent,
    CustomInfrastRoomGroupsMatchFailedEvent,
    CustomInfrastRoomOperatorsEvent,
    DeepExplorationCompletedEvent,
    DepotEvent,
    DetectOperatorsCompletedEvent,
    DetectOperatorsErrorEvent,
    DetectOperatorsStartedEvent,
    DropItem,
    EncounterOcrErrorEvent,
    ExceededLimitEvent,
    FacilityEvent,
    FightTimesEvent,
    FinishedEvent,
    FoldartalGainOcrNextLevelEvent,
    InfrastConfirmButtonEvent,
    InfrastTrainingCompletedEvent,
    InfrastTrainingIdleEvent,
    InfrastTrainingTimeLeftEvent,
    MatchDeploymentCompletedEvent,
    MatchDeploymentErrorEvent,
    MatchDeploymentStartedEvent,
    MonthlySquadCompletedEvent,
    OperBoxEvent,
    OperBoxOper,
    OwnedOperBoxOper,
    ProcessTaskEvent,
    ProductChangeFailEvent,
    ProductChangedEvent,
    ProductIncorrectEvent,
    RecruitErrorEvent,
    RecruitNoPermitEvent,
    RecruitOption,
    RecruitResultEvent,
    RecruitResultOper,
    RecruitTagsDetectedEvent,
    RecruitTagsRefreshedEvent,
    RecruitTagsSelectedEvent,
    RoguelikeCollapsalParadigmsEvent,
    RoguelikeCombatEndEvent,
    RoguelikeCoppersExchangeInfoEvent,
    RoguelikeCoppersRecognitionErrorEvent,
    RoguelikeEncounterOption,
    RoguelikeEncounterOptionsEvent,
    RoguelikeEventInfoEvent,
    RoguelikeInvestmentEvent,
    RoguelikeInvestmentReachFullEvent,
    RoguelikeInvestmentReachLimitEvent,
    RoguelikeJieGardenTargetFoundEvent,
    RoguelikeSettlementEvent,
    SSSGamePassEvent,
    SSSSettlementEvent,
    SSSStageEvent,
    SanityBeforeStageEvent,
    SideStoryReopenTaskNotExistsEvent,
    SliceCompletedEvent,
    SliceErrorEvent,
    SliceStartedEvent,
    StageDropsEvent,
    StageInfo,
    StageInfoErrorEvent,
    StageInfoEvent,
    StageQueueMissionCompletedEvent,
    StageQueueStageNotFoundEvent,
    StageQueueUnableToAgentEvent,
    StatItem,
    SubTaskCompletedEvent,
    SubTaskErrorEvent,
    SubTaskStartedEvent,
    SubTaskStoppedEvent,
    UnsupportedLevelEvent,
    UseMedicineEvent,
    UserAdditionalOperInvalidEvent,
)
from ..events.taskchain_events import (
    RoutingRestartTaskChainEvent,
    TaskChainCompletedEvent,
    TaskChainErrorEvent,
    TaskChainExtraInfoEvent,
    TaskChainStartEvent,
    TaskChainStoppedEvent,
)
from .common import (
    _EventFactory,
    _MsgParser,
    _SubTaskExtraParser,
    _SubtaskEventKwargs,
    _decode_struct,
)
from .payloads import (
    AccountSwitchDetails,
    AllTasksCompletedPayload,
    AsyncCallInfoPayload,
    BattleFormationDetails,
    BattleFormationOperUnavailableDetails,
    BattleFormationSelectedDetails,
    BoskyPassageNodeDetails,
    ConnectionInfoPayload,
    CopilotActionDetails,
    CopilotListLoadTaskFileSuccessDetails,
    CreditFullOnlyBuyDiscountDetails,
    CustomInfrastRoomGroupsMatchDetails,
    CustomInfrastRoomGroupsMatchFailedDetails,
    CustomInfrastRoomOperatorsDetails,
    DepotDetails,
    DropItemPayload,
    ExceededLimitDetails,
    FacilityDetails,
    FightTimesDetails,
    FinishedDetails,
    FoldartalGainOcrNextLevelDetails,
    InfrastTrainingCompletedDetails,
    InfrastTrainingTimeLeftDetails,
    InitFailedPayload,
    OperBoxDetails,
    OperBoxOperPayload,
    OwnedOperBoxOperPayload,
    ProcessTaskDetails,
    ProductDetails,
    RecruitErrorDetails,
    RecruitNoPermitDetails,
    RecruitResultDetails,
    RecruitResultOperPayload,
    RecruitResultOptionPayload,
    RecruitSingleTagDetails,
    RecruitTagsDetectedDetails,
    RecruitTagsRefreshedDetails,
    RecruitTagsSelectedDetails,
    ReportRequestPayload,
    RoguelikeCollapsalParadigmsDetails,
    RoguelikeCoppersExchangeInfoDetails,
    RoguelikeCoppersRecognitionErrorDetails,
    RoguelikeEncounterOptionsDetails,
    RoguelikeEventDetails,
    RoguelikeInvestmentDetails,
    RoguelikeInvestmentReachLimitDetails,
    RoguelikeJieGardenTargetFoundDetails,
    RoguelikeSettlementDetails,
    SSSStageDetails,
    SanityBeforeStageDetails,
    ScreencapAlternativePayload,
    StageCodeDetails,
    StageDropsDetails,
    StageInfoPayload,
    StageNameDetails,
    StageQueueMissionCompletedDetails,
    StatItemPayload,
    SubTaskPayload,
    SubTaskStartDetails,
    TaskChainPayload,
    UnsupportedLevelDetails,
    UseMedicineDetails,
    UserAdditionalOperInvalidDetails,
)


# ── 转换辅助函数 ──

_SUBTASK_PROCESS_TASK = "ProcessTask"


def _drop_item_from_payload(item: DropItemPayload) -> DropItem:
    return DropItem(item_id=item.itemId, item_name=item.itemName, quantity=item.quantity)


def _stage_info_from_payload(item: StageInfoPayload) -> StageInfo:
    return StageInfo(stage_code=item.stageCode, stage_id=item.stageId)


def _stat_item_from_payload(item: StatItemPayload) -> StatItem:
    return StatItem(
        item_id=item.itemId,
        item_name=item.itemName,
        quantity=item.quantity,
        add_quantity=item.addQuantity,
    )


def _recruit_option_from_payload(item: RecruitResultOptionPayload) -> RecruitOption:
    return RecruitOption(
        tags=list(item.tags),
        level=item.level,
        opers=[_recruit_result_oper_from_payload(oper) for oper in item.opers],
    )


def _recruit_result_oper_from_payload(item: RecruitResultOperPayload) -> RecruitResultOper:
    return RecruitResultOper(name=item.name, id=item.id, level=item.level)


def _oper_box_oper_from_payload(item: OperBoxOperPayload) -> OperBoxOper:
    return OperBoxOper(
        id=item.id, name=item.name,
        name_en=item.name_en, name_jp=item.name_jp,
        name_kr=item.name_kr, name_tw=item.name_tw,
        rarity=item.rarity, own=item.own,
    )


def _owned_oper_box_oper_from_payload(item: OwnedOperBoxOperPayload) -> OwnedOperBoxOper:
    return OwnedOperBoxOper(
        id=item.id, name=item.name, own=item.own,
        elite=item.elite, level=item.level,
        potential=item.potential, rarity=item.rarity,
    )


def _screencap_alternative(item: ScreencapAlternativePayload) -> ScreencapMethodAlternative:
    return ScreencapMethodAlternative(method=item.method, cost=item.cost)


# ── CallbackParser ──

class CallbackParser:
    """集中处理所有 MaaCore 回调 JSON 的解析与路由。

    不使用 mixin 继承——所有解析方法都是此类的普通方法，
    分发表在 __init__ 中基于 SubTaskWhat 等常量构建。
    """

    def __init__(self) -> None:
        # ── 一级路由：msg id → parser ──
        self._msg_dispatch: dict[AsstMsg, _MsgParser] = {
            AsstMsg.INTERNAL_ERROR: self._parse_internal_error,
            AsstMsg.INIT_FAILED: self._parse_init_failed,
            AsstMsg.CONNECTION_INFO: self._parse_connection_info,
            AsstMsg.ALL_TASKS_COMPLETED: self._parse_all_tasks_completed,
            AsstMsg.ASYNC_CALL_INFO: self._parse_async_call_info,
            AsstMsg.DESTROYED: self._parse_destroyed,
            AsstMsg.TASK_CHAIN_ERROR: self._parse_taskchain,
            AsstMsg.TASK_CHAIN_START: self._parse_taskchain,
            AsstMsg.TASK_CHAIN_COMPLETED: self._parse_taskchain,
            AsstMsg.TASK_CHAIN_EXTRA_INFO: self._parse_taskchain,
            AsstMsg.TASK_CHAIN_STOPPED: self._parse_taskchain,
            AsstMsg.SUB_TASK_ERROR: self._parse_subtask,
            AsstMsg.SUB_TASK_START: self._parse_subtask,
            AsstMsg.SUB_TASK_COMPLETED: self._parse_subtask,
            AsstMsg.SUB_TASK_EXTRA_INFO: self._parse_subtask,
            AsstMsg.SUB_TASK_STOPPED: self._parse_subtask,
            AsstMsg.REPORT_REQUEST: self._parse_report_request,
        }

        # ── 任务链事件类映射 ──
        self._taskchain_event_classes: dict[AsstMsg, _EventFactory] = {
            AsstMsg.TASK_CHAIN_ERROR: TaskChainErrorEvent,
            AsstMsg.TASK_CHAIN_START: TaskChainStartEvent,
            AsstMsg.TASK_CHAIN_COMPLETED: TaskChainCompletedEvent,
            AsstMsg.TASK_CHAIN_EXTRA_INFO: TaskChainExtraInfoEvent,
            AsstMsg.TASK_CHAIN_STOPPED: TaskChainStoppedEvent,
        }

        # ── 子任务基础事件类映射 ──
        self._subtask_event_classes: dict[AsstMsg, _EventFactory] = {
            AsstMsg.SUB_TASK_ERROR: SubTaskErrorEvent,
            AsstMsg.SUB_TASK_START: SubTaskStartedEvent,
            AsstMsg.SUB_TASK_COMPLETED: SubTaskCompletedEvent,
            AsstMsg.SUB_TASK_STOPPED: SubTaskStoppedEvent,
        }

        # ── 命名子任务事件（特定 subtask 名称 → 特定事件类） ──
        self._subtask_named_event_classes: dict[tuple[AsstMsg, str], _EventFactory] = {
            (AsstMsg.SUB_TASK_START, "MatchDeployment"): MatchDeploymentStartedEvent,
            (AsstMsg.SUB_TASK_COMPLETED, "MatchDeployment"): MatchDeploymentCompletedEvent,
            (AsstMsg.SUB_TASK_ERROR, "MatchDeployment"): MatchDeploymentErrorEvent,
            (AsstMsg.SUB_TASK_START, "Slice"): SliceStartedEvent,
            (AsstMsg.SUB_TASK_COMPLETED, "Slice"): SliceCompletedEvent,
            (AsstMsg.SUB_TASK_ERROR, "Slice"): SliceErrorEvent,
            (AsstMsg.SUB_TASK_START, "CompSkill"): CompSkillStartedEvent,
            (AsstMsg.SUB_TASK_COMPLETED, "CompSkill"): CompSkillCompletedEvent,
            (AsstMsg.SUB_TASK_ERROR, "CompSkill"): CompSkillErrorEvent,
            (AsstMsg.SUB_TASK_START, "DetectOperators"): DetectOperatorsStartedEvent,
            (AsstMsg.SUB_TASK_COMPLETED, "DetectOperators"): DetectOperatorsCompletedEvent,
            (AsstMsg.SUB_TASK_ERROR, "DetectOperators"): DetectOperatorsErrorEvent,
            (AsstMsg.SUB_TASK_START, "ClassifyDirection"): ClassifyDirectionStartedEvent,
            (AsstMsg.SUB_TASK_COMPLETED, "ClassifyDirection"): ClassifyDirectionCompletedEvent,
            (AsstMsg.SUB_TASK_ERROR, "ClassifyDirection"): ClassifyDirectionErrorEvent,
        }

        # ── ExtraInfo 解析器 (what → parser) ──
        self._subtask_extra_parsers: dict[str, _SubTaskExtraParser] = {
            SubTaskWhat.STAGE_DROPS: self._parse_stage_drops,
            SubTaskWhat.EXCEEDED_LIMIT: self._parse_exceeded_limit,
            SubTaskWhat.RECRUIT_TAGS_DETECTED: self._parse_recruit_tags_detected,
            SubTaskWhat.RECRUIT_SPECIAL_TAG: self._parse_recruit_special_tag,
            SubTaskWhat.RECRUIT_PRESERVED_TAG: self._parse_recruit_preserved_tag,
            SubTaskWhat.RECRUIT_RESULT: self._parse_recruit_result,
            SubTaskWhat.RECRUIT_TAGS_REFRESHED: self._parse_recruit_tags_refreshed,
            SubTaskWhat.RECRUIT_TAGS_SELECTED: self._parse_recruit_tags_selected,
            SubTaskWhat.RECRUIT_NO_PERMIT: self._parse_recruit_no_permit,
            SubTaskWhat.ENTER_FACILITY: self._parse_facility,
            SubTaskWhat.NOT_ENOUGH_STAFF: self._parse_facility,
            SubTaskWhat.PRODUCT_OF_FACILITY: self._parse_facility,
            SubTaskWhat.STAGE_INFO: self._parse_stage_info,
            SubTaskWhat.STAGE_INFO_ERROR: self._parse_simple_subtask_extra,
            SubTaskWhat.OPER_BOX: self._parse_operbox,
            SubTaskWhat.DEPOT: self._parse_depot,
            SubTaskWhat.PRODUCT_INCORRECT: self._parse_product_incorrect,
            SubTaskWhat.PRODUCT_CHANGED: self._parse_product_changed,
            SubTaskWhat.PRODUCT_CHANGE_FAIL: self._parse_product_change_fail,
            SubTaskWhat.CREDIT_FULL_ONLY_BUY_DISCOUNT: self._parse_credit_full_only_buy_discount,
            SubTaskWhat.CUSTOM_INFRAST_ROOM_GROUPS_MATCH: self._parse_custom_infrast_room_groups_match,
            SubTaskWhat.CUSTOM_INFRAST_ROOM_GROUPS_MATCH_FAILED: self._parse_custom_infrast_room_groups_match_failed,
            SubTaskWhat.CUSTOM_INFRAST_ROOM_OPERATORS: self._parse_custom_infrast_room_operators,
            SubTaskWhat.INFRAST_CONFIRM_BUTTON: self._parse_simple_subtask_extra,
            SubTaskWhat.INFRAST_TRAINING_IDLE: self._parse_simple_subtask_extra,
            SubTaskWhat.INFRAST_TRAINING_COMPLETED: self._parse_infrast_training_completed,
            SubTaskWhat.INFRAST_TRAINING_TIME_LEFT: self._parse_infrast_training_time_left,
            SubTaskWhat.BATTLE_FORMATION: self._parse_battle_formation,
            SubTaskWhat.BATTLE_FORMATION_SELECTED: self._parse_battle_formation_selected,
            SubTaskWhat.BATTLE_FORMATION_OPER_UNAVAILABLE: self._parse_battle_formation_oper_unavailable,
            SubTaskWhat.BATTLE_FORMATION_PARSE_FAILED: self._parse_simple_subtask_extra,
            SubTaskWhat.ACCOUNT_SWITCH: self._parse_account_switch,
            SubTaskWhat.COPILOT_ACTION: self._parse_copilot_action,
            SubTaskWhat.COPILOT_LIST_LOAD_TASK_FILE_SUCCESS: self._parse_copilot_list_load_task_file_success,
            SubTaskWhat.FINISHED: self._parse_finished,
            SubTaskWhat.MONTHLY_SQUAD_COMPLETED: self._parse_simple_subtask_extra,
            SubTaskWhat.DEEP_EXPLORATION_COMPLETED: self._parse_simple_subtask_extra,
            SubTaskWhat.ENCOUNTER_OCR_ERROR: self._parse_simple_subtask_extra,
            SubTaskWhat.ROGUELIKE_COMBAT_END: self._parse_simple_subtask_extra,
            SubTaskWhat.ROGUELIKE_EVENT: self._parse_roguelike_event,
            SubTaskWhat.ROGUELIKE_ENCOUNTER_OPTIONS: self._parse_roguelike_encounter_options,
            SubTaskWhat.BOSKY_PASSAGE_NODE: self._parse_bosky_passage_node,
            SubTaskWhat.ROGUELIKE_COPPERS_EXCHANGE_INFO: self._parse_roguelike_coppers_exchange_info,
            SubTaskWhat.ROGUELIKE_COPPERS_RECOGNITION_ERROR: self._parse_roguelike_coppers_recognition_error,
            SubTaskWhat.ROGUELIKE_JIE_GARDEN_TARGET_FOUND: self._parse_roguelike_jie_garden_target_found,
            SubTaskWhat.FOLDARTAL_GAIN_OCR_NEXT_LEVEL: self._parse_foldartal_gain_ocr_next_level,
            SubTaskWhat.ROGUELIKE_COLLAPSAL_PARADIGMS: self._parse_roguelike_collapsal_paradigms,
            SubTaskWhat.ROGUELIKE_INVESTMENT: self._parse_roguelike_investment,
            SubTaskWhat.ROGUELIKE_INVESTMENT_REACH_LIMIT: self._parse_roguelike_investment_reach_limit,
            SubTaskWhat.ROGUELIKE_INVESTMENT_REACH_FULL: self._parse_simple_subtask_extra,
            SubTaskWhat.ROGUELIKE_SETTLEMENT: self._parse_roguelike_settlement,
            SubTaskWhat.SANITY_BEFORE_STAGE: self._parse_sanity_before_stage,
            SubTaskWhat.FIGHT_TIMES: self._parse_fight_times,
            SubTaskWhat.USE_MEDICINE: self._parse_use_medicine,
            SubTaskWhat.STAGE_QUEUE_STAGE_NOT_FOUND: self._parse_stage_queue_stage_not_found,
            SubTaskWhat.STAGE_QUEUE_UNABLE_TO_AGENT: self._parse_stage_queue_unable_to_agent,
            SubTaskWhat.STAGE_QUEUE_MISSION_COMPLETED: self._parse_stage_queue_mission_completed,
            SubTaskWhat.SIDE_STORY_REOPEN_TASK_NOT_EXISTS: self._parse_simple_subtask_extra,
            SubTaskWhat.UNSUPPORTED_LEVEL: self._parse_unsupported_level,
            SubTaskWhat.SSS_STAGE: self._parse_sss_stage,
            SubTaskWhat.SSS_SETTLEMENT: self._parse_simple_subtask_extra,
            SubTaskWhat.SSS_GAME_PASS: self._parse_simple_subtask_extra,
        }

        # ── Error 解析器 (what → parser) ──
        self._subtask_error_parsers: dict[str, _SubTaskExtraParser] = {
            SubTaskWhat.RECRUIT_ERROR: self._parse_recruit_error,
            "UserAdditionalOperInvalid": self._parse_user_additional_oper_invalid,
        }

        # ── 简单事件类映射 (what → event class) ──
        self._subtask_extra_simple_event_classes: dict[str, _EventFactory] = {
            SubTaskWhat.STAGE_INFO_ERROR: StageInfoErrorEvent,
            SubTaskWhat.MONTHLY_SQUAD_COMPLETED: MonthlySquadCompletedEvent,
            SubTaskWhat.DEEP_EXPLORATION_COMPLETED: DeepExplorationCompletedEvent,
            SubTaskWhat.PRODUCT_CHANGE_FAIL: ProductChangeFailEvent,
            SubTaskWhat.INFRAST_CONFIRM_BUTTON: InfrastConfirmButtonEvent,
            SubTaskWhat.INFRAST_TRAINING_IDLE: InfrastTrainingIdleEvent,
            SubTaskWhat.BATTLE_FORMATION_PARSE_FAILED: BattleFormationParseFailedEvent,
            SubTaskWhat.ENCOUNTER_OCR_ERROR: EncounterOcrErrorEvent,
            SubTaskWhat.ROGUELIKE_COMBAT_END: RoguelikeCombatEndEvent,
            SubTaskWhat.ROGUELIKE_INVESTMENT_REACH_FULL: RoguelikeInvestmentReachFullEvent,
            SubTaskWhat.SSS_SETTLEMENT: SSSSettlementEvent,
            SubTaskWhat.SSS_GAME_PASS: SSSGamePassEvent,
            SubTaskWhat.SIDE_STORY_REOPEN_TASK_NOT_EXISTS: SideStoryReopenTaskNotExistsEvent,
        }

    # ── 入口 ──

    def parse_and_route(self, msg: int, data: JsonDict) -> Event | None:
        try:
            msg_id = AsstMsg(msg)
        except ValueError:
            raise msgspec.ValidationError(f"unknown callback msg: {msg}") from None
        parser = self._msg_dispatch.get(msg_id)
        if parser is not None:
            return parser(msg_id, data)
        raise msgspec.ValidationError(f"unhandled callback msg: {msg_id.name}")

    def make_callback_error(self, msg: int, source: str, exc: BaseException) -> CallbackErrorEvent:
        return CallbackErrorEvent(
            msg=msg, uuid="",
            source=source,
            error=f"{type(exc).__name__}: {exc}",
        )

    # ── 全局事件解析 ──

    def _parse_internal_error(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        del data
        return InternalErrorEvent(msg=int(msg_id), uuid="")

    def _parse_init_failed(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, InitFailedPayload, "callback")
        return InitFailedEvent(msg=int(msg_id), uuid="", what=payload.what, why=payload.why)

    def _parse_connection_info(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, ConnectionInfoPayload, "callback")
        details = payload.details
        what = payload.what
        common_kwargs = {
            "msg": int(msg_id), "uuid": payload.uuid, "what": what, "why": payload.why,
            "connected": what in (ConnectionWhat.CONNECTED, ConnectionWhat.UUID_GOT),
        }

        if what == ConnectionWhat.CONNECT_FAILED:
            return ConnectFailedConnectionEvent(**common_kwargs,
                adb=details.adb, address=details.address, config=details.config, adb_output=details.adb_output)
        if what == ConnectionWhat.CONNECTED:
            return ConnectedConnectionEvent(**common_kwargs,
                adb=details.adb, address=details.address, config=details.config)
        if what == ConnectionWhat.UUID_GOT:
            return UuidGotConnectionEvent(**common_kwargs,
                adb=details.adb, address=details.address, config=details.config, device_uuid=details.uuid)
        if what == ConnectionWhat.UNSUPPORTED_RESOLUTION:
            return UnsupportedResolutionConnectionEvent(**common_kwargs,
                width=details.width or payload.width, height=details.height or payload.height)
        if what == ConnectionWhat.RESOLUTION_INFO:
            return ResolutionInfoConnectionEvent(**common_kwargs,
                width=details.width or payload.width, height=details.height or payload.height)
        if what == ConnectionWhat.RESOLUTION_GOT:
            return ResolutionGotConnectionEvent(**common_kwargs,
                adb=details.adb, address=details.address, config=details.config,
                width=details.width or payload.width, height=details.height or payload.height)
        if what == ConnectionWhat.RESOLUTION_ERROR:
            return ResolutionErrorConnectionEvent(**common_kwargs,
                adb=details.adb, address=details.address, config=details.config,
                width=details.width or payload.width, height=details.height or payload.height)
        if what == ConnectionWhat.RECONNECTING:
            return ReconnectingConnectionEvent(**common_kwargs,
                reconnect=details.reconnect, cmd=details.cmd, times=details.times)
        if what == ConnectionWhat.RECONNECTED:
            return ReconnectedConnectionEvent(**common_kwargs,
                reconnect=details.reconnect, cmd=details.cmd, times=details.times)
        if what == ConnectionWhat.DISCONNECT:
            return DisconnectConnectionEvent(**common_kwargs,
                reconnect=details.reconnect, cmd=details.cmd, times=details.times)
        if what == ConnectionWhat.SCREENCAP_FAILED:
            return ScreencapFailedConnectionEvent(**common_kwargs)
        if what == ConnectionWhat.TOUCH_MODE_NOT_AVAILABLE:
            return TouchModeNotAvailableConnectionEvent(**common_kwargs,
                adb=details.adb, address=details.address, config=details.config)
        if what == ConnectionWhat.FASTEST_WAY_TO_SCREENCAP:
            return FastestWayToScreencapConnectionEvent(**common_kwargs,
                method=details.method, cost=details.cost,
                alternatives=[_screencap_alternative(item) for item in details.alternatives])
        if what == ConnectionWhat.SCREENCAP_COST:
            return ScreencapCostConnectionEvent(**common_kwargs,
                min_cost=details.min_cost, max_cost=details.max_cost,
                avg_cost=details.avg_cost, fault_times=details.fault_times)
        if what == ConnectionWhat.UNSUPPORTED_PLAY_TOOLS:
            return UnsupportedPlayToolsConnectionEvent(**common_kwargs)
        raise msgspec.ValidationError(f"unknown ConnectionInfo what: {what}")

    def _parse_all_tasks_completed(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, AllTasksCompletedPayload, "callback")
        return AllTasksCompletedEvent(
            msg=int(msg_id), uuid=payload.uuid,
            taskchain=payload.taskchain, finished_tasks=list(payload.finished_tasks))

    def _parse_async_call_info(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, AsyncCallInfoPayload, "callback")
        common_kwargs = {
            "msg": int(msg_id), "uuid": payload.uuid, "what": payload.what,
            "async_call_id": payload.async_call_id, "ret": payload.details.ret, "cost": payload.details.cost,
        }
        what = payload.what
        if what == AsyncCallWhat.CONNECT:
            return ConnectAsyncCallInfoEvent(**common_kwargs)
        if what == AsyncCallWhat.ATTACH_WINDOW:
            return AttachWindowAsyncCallInfoEvent(**common_kwargs)
        if what == AsyncCallWhat.CLICK:
            return ClickAsyncCallInfoEvent(**common_kwargs)
        if what == AsyncCallWhat.SCREENCAP:
            return ScreencapAsyncCallInfoEvent(**common_kwargs)
        if what == AsyncCallWhat.UNKNOWN:
            return UnknownAsyncCallInfoEvent(**common_kwargs)
        raise msgspec.ValidationError(f"unknown AsyncCallInfo what: {what}")

    def _parse_destroyed(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, TaskChainPayload, "callback")
        return DestroyedEvent(msg=int(msg_id), uuid=payload.uuid)

    def _parse_report_request(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, ReportRequestPayload, "callback")
        return ReportRequestEvent(
            msg=int(msg_id), uuid=payload.uuid,
            url=payload.url, headers=dict(payload.headers),
            body=payload.body, subtask=payload.subtask)

    # ── 任务链事件解析 ──

    def _parse_taskchain(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, TaskChainPayload, "callback")
        if msg_id == AsstMsg.TASK_CHAIN_EXTRA_INFO:
            common_kwargs = {
                "msg": int(msg_id), "uuid": payload.uuid,
                "taskchain": payload.taskchain, "taskid": payload.taskid,
                "what": payload.what, "why": payload.why,
            }
            if payload.what == "RoutingRestart":
                return RoutingRestartTaskChainEvent(**common_kwargs, node_cost=payload.node_cost)
            return TaskChainExtraInfoEvent(**common_kwargs)

        event_class = self._taskchain_event_classes.get(msg_id)
        if event_class is None:
            raise msgspec.ValidationError(f"unhandled taskchain msg: {msg_id.name}")
        return event_class(
            msg=int(msg_id), uuid=payload.uuid,
            taskchain=payload.taskchain, taskid=payload.taskid)

    # ── 子任务事件解析 ──

    def _parse_subtask(self, msg_id: AsstMsg, data: JsonDict) -> Event:
        payload = _decode_struct(data, SubTaskPayload, "callback")
        msg = int(msg_id)
        common_kwargs: _SubtaskEventKwargs = {
            "msg": msg, "uuid": payload.uuid,
            "subtask": payload.subtask, "class_name": payload.class_name,
            "taskchain": payload.taskchain, "taskid": payload.taskid,
            "what": payload.what, "why": payload.why,
        }

        if msg_id == AsstMsg.SUB_TASK_EXTRA_INFO:
            return self._parse_subtask_extra(data, **common_kwargs)

        if msg_id == AsstMsg.SUB_TASK_ERROR:
            parser = self._subtask_error_parsers.get(common_kwargs["what"])
            if parser is not None:
                return parser(data, **common_kwargs)

        event_class = self._subtask_named_event_classes.get((msg_id, common_kwargs["what"]))
        if event_class is None:
            event_class = self._subtask_event_classes.get(msg_id)
        if event_class is None:
            raise msgspec.ValidationError(f"unhandled subtask msg: {msg_id.name}")

        if msg_id == AsstMsg.SUB_TASK_START:
            details = _decode_struct(data.get("details"), SubTaskStartDetails, "details")
            return event_class(**common_kwargs, task_name=details.task)

        return event_class(**common_kwargs)

    def _parse_subtask_extra(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        parser = self._subtask_extra_parsers.get(kwargs["what"])
        if parser is not None:
            return parser(data, **kwargs)

        if kwargs["subtask"] == _SUBTASK_PROCESS_TASK:
            return self._parse_process_task(data, **kwargs)

        raise msgspec.ValidationError(f"unknown subtask extra what: {kwargs['what']}")

    # ── 简单子任务事件 ──

    def _parse_simple_subtask_extra(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        del data
        event_class = self._subtask_extra_simple_event_classes.get(kwargs["what"])
        if event_class is None:
            raise msgspec.ValidationError(f"unsupported simple subtask event: {kwargs['what']}")
        return event_class(**kwargs)

    # ── 结构化子任务解析 ──

    def _parse_process_task(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), ProcessTaskDetails, "details")
        return ProcessTaskEvent(**kwargs,
            task_name=details.task, exec_times=details.exec_times,
            max_times=details.max_times, action=details.action, algorithm=details.algorithm)

    def _parse_stage_drops(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), StageDropsDetails, "details")
        return StageDropsEvent(**kwargs,
            drops=[_drop_item_from_payload(item) for item in details.drops],
            stage=StageInfo() if details.stage is None else _stage_info_from_payload(details.stage),
            stars=details.stars,
            stats=[_stat_item_from_payload(item) for item in details.stats])

    def _parse_exceeded_limit(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), ExceededLimitDetails, "details")
        return ExceededLimitEvent(**kwargs,
            task_name=details.task, exec_times=details.exec_times, max_times=details.max_times)

    def _parse_recruit_tags_detected(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitTagsDetectedDetails, "details")
        return RecruitTagsDetectedEvent(**kwargs, tags=list(details.tags))

    def _parse_recruit_special_tag(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitSingleTagDetails, "details")
        return RecruitTagsDetectedEvent(**kwargs, tags=[details.tag])

    def _parse_recruit_preserved_tag(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitSingleTagDetails, "details")
        return RecruitTagsDetectedEvent(**kwargs, tags=[details.tag])

    def _parse_recruit_result(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitResultDetails, "details")
        return RecruitResultEvent(**kwargs,
            tags=list(details.tags), level=details.level,
            result=[_recruit_option_from_payload(item) for item in details.result])

    def _parse_recruit_tags_refreshed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitTagsRefreshedDetails, "details")
        return RecruitTagsRefreshedEvent(**kwargs, count=details.count, refresh_limit=details.refresh_limit)

    def _parse_recruit_tags_selected(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitTagsSelectedDetails, "details")
        return RecruitTagsSelectedEvent(**kwargs, tags=list(details.tags))

    def _parse_recruit_no_permit(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitNoPermitDetails, "details")
        return RecruitNoPermitEvent(**kwargs, continue_refresh=details.continue_refresh)

    def _parse_recruit_error(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitErrorDetails, "details")
        return RecruitErrorEvent(**kwargs, refresh_limit=details.refresh_limit)

    def _parse_facility(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), FacilityDetails, "details")
        return FacilityEvent(**kwargs, facility=details.facility, index=details.index, product=details.product)

    def _parse_stage_info(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), StageNameDetails, "details")
        return StageInfoEvent(**kwargs, name=details.name)

    def _parse_product_incorrect(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), ProductDetails, "details")
        return ProductIncorrectEvent(**kwargs, product=details.product)

    def _parse_product_changed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), ProductDetails, "details")
        return ProductChangedEvent(**kwargs, product=details.product)

    def _parse_product_change_fail(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_simple_subtask_extra(data, **kwargs)

    def _parse_credit_full_only_buy_discount(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CreditFullOnlyBuyDiscountDetails, "details")
        return CreditFullOnlyBuyDiscountEvent(**kwargs, credit=details.credit)

    def _parse_custom_infrast_room_groups_match(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CustomInfrastRoomGroupsMatchDetails, "details")
        return CustomInfrastRoomGroupsMatchEvent(**kwargs, group=details.group)

    def _parse_custom_infrast_room_groups_match_failed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CustomInfrastRoomGroupsMatchFailedDetails, "details")
        return CustomInfrastRoomGroupsMatchFailedEvent(**kwargs, groups=list(details.groups))

    def _parse_custom_infrast_room_operators(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CustomInfrastRoomOperatorsDetails, "details")
        return CustomInfrastRoomOperatorsEvent(**kwargs, names=list(details.names), candidates=list(details.candidates))

    def _parse_finished(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), FinishedDetails, "details")
        return FinishedEvent(**kwargs, file_name=details.filename)

    def _parse_battle_formation(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), BattleFormationDetails, "details")
        return BattleFormationEvent(**kwargs, formation=list(details.formation))

    def _parse_battle_formation_selected(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), BattleFormationSelectedDetails, "details")
        return BattleFormationSelectedEvent(**kwargs, selected=details.selected, group_name=details.group_name)

    def _parse_battle_formation_oper_unavailable(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), BattleFormationOperUnavailableDetails, "details")
        return BattleFormationOperUnavailableEvent(**kwargs, oper_name=details.oper_name, requirement_type=details.requirement_type)

    def _parse_account_switch(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), AccountSwitchDetails, "details")
        return AccountSwitchEvent(**kwargs, account_name=details.account_name)

    def _parse_copilot_action(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CopilotActionDetails, "details")
        return CopilotActionEvent(**kwargs,
            action=details.action, target=details.target, doc=details.doc,
            doc_color=details.doc_color, elapsed_time=details.elapsed_time)

    def _parse_copilot_list_load_task_file_success(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CopilotListLoadTaskFileSuccessDetails, "details")
        return CopilotListLoadTaskFileSuccessEvent(**kwargs, stage_name=details.stage_name, file_name=details.file_name)

    def _parse_user_additional_oper_invalid(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), UserAdditionalOperInvalidDetails, "details")
        return UserAdditionalOperInvalidEvent(**kwargs, name=details.name)

    def _parse_sanity_before_stage(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), SanityBeforeStageDetails, "details")
        return SanityBeforeStageEvent(**kwargs,
            report_time=details.report_time, current_sanity=details.current_sanity, max_sanity=details.max_sanity)

    def _parse_fight_times(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), FightTimesDetails, "details")
        return FightTimesEvent(**kwargs,
            times_finished=details.times_finished, series=details.series,
            sanity_cost=details.sanity_cost, finished=details.finished)

    def _parse_use_medicine(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), UseMedicineDetails, "details")
        return UseMedicineEvent(**kwargs, is_expiring=details.is_expiring, count=details.count)

    def _parse_stage_code_event(self, event_class: _EventFactory, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), StageCodeDetails, "details")
        return event_class(**kwargs, stage_code=details.stage_code)

    def _parse_stage_queue_stage_not_found(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_stage_code_event(StageQueueStageNotFoundEvent, data, **kwargs)

    def _parse_stage_queue_unable_to_agent(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_stage_code_event(StageQueueUnableToAgentEvent, data, **kwargs)

    def _parse_stage_queue_mission_completed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), StageQueueMissionCompletedDetails, "details")
        return StageQueueMissionCompletedEvent(**kwargs, stage_code=details.stage_code, stars=details.stars)

    def _parse_unsupported_level(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), UnsupportedLevelDetails, "details")
        return UnsupportedLevelEvent(**kwargs, level=details.level)

    def _parse_sss_stage(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), SSSStageDetails, "details")
        return SSSStageEvent(**kwargs, stage=details.stage)

    def _parse_operbox(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), OperBoxDetails, "details")
        return OperBoxEvent(**kwargs,
            done=details.done,
            all_opers=[_oper_box_oper_from_payload(item) for item in details.all_opers],
            own_opers=[_owned_oper_box_oper_from_payload(item) for item in details.own_opers])

    def _parse_depot(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), DepotDetails, "details")
        parsed: dict[str, int] = {}
        if details.data:
            parsed = msgspec.json.decode(details.data.encode(), type=dict[str, int])
        return DepotEvent(**kwargs, done=details.done, items=parsed)

    def _parse_infrast_training_completed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), InfrastTrainingCompletedDetails, "details")
        return InfrastTrainingCompletedEvent(**kwargs, operator=details.operator, skill=details.skill, level=details.level)

    def _parse_infrast_training_time_left(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), InfrastTrainingTimeLeftDetails, "details")
        return InfrastTrainingTimeLeftEvent(**kwargs, operator=details.operator, skill=details.skill, level=details.level, time=details.time)

    # ── 肉鸽解析 ──

    def _parse_roguelike_event(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeEventDetails, "details")
        return RoguelikeEventInfoEvent(**kwargs, name=details.name, default_choose=details.default_choose, choose_option=details.choose_option)

    def _parse_roguelike_encounter_options(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeEncounterOptionsDetails, "details")
        return RoguelikeEncounterOptionsEvent(**kwargs,
            options=[RoguelikeEncounterOption(enabled=item.enabled, text=item.text) for item in details.options])

    def _parse_bosky_passage_node(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), BoskyPassageNodeDetails, "details")
        return BoskyPassageNodeEvent(**kwargs, node_type=details.node_type)

    def _parse_roguelike_coppers_exchange_info(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeCoppersExchangeInfoDetails, "details")
        return RoguelikeCoppersExchangeInfoEvent(**kwargs, to_discard=details.to_discard, to_pickup=details.to_pickup)

    def _parse_roguelike_coppers_recognition_error(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeCoppersRecognitionErrorDetails, "details")
        return RoguelikeCoppersRecognitionErrorEvent(**kwargs, recognized_name=details.recognized_name)

    def _parse_roguelike_jie_garden_target_found(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeJieGardenTargetFoundDetails, "details")
        return RoguelikeJieGardenTargetFoundEvent(**kwargs, target_subtype=details.target_subtype)

    def _parse_foldartal_gain_ocr_next_level(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), FoldartalGainOcrNextLevelDetails, "details")
        return FoldartalGainOcrNextLevelEvent(**kwargs, foldartal=details.foldartal)

    def _parse_roguelike_collapsal_paradigms(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeCollapsalParadigmsDetails, "details")
        return RoguelikeCollapsalParadigmsEvent(**kwargs, cur=details.cur, deepen_or_weaken=details.deepen_or_weaken, prev=details.prev)

    def _parse_roguelike_investment(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeInvestmentDetails, "details")
        return RoguelikeInvestmentEvent(**kwargs, count=details.count, total=details.total, deposit=details.deposit)

    def _parse_roguelike_investment_reach_limit(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeInvestmentReachLimitDetails, "details")
        return RoguelikeInvestmentReachLimitEvent(**kwargs, limit=details.limit)

    def _parse_roguelike_settlement(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeSettlementDetails, "details")
        return RoguelikeSettlementEvent(**kwargs,
            game_pass=details.game_pass, floor=details.floor, step=details.step,
            combat=details.combat, recruit=details.recruit, collection=details.collection,
            boss=details.boss, emergency=details.emergency, difficulty=details.difficulty,
            score=details.score, exp=details.exp, skill=details.skill)
