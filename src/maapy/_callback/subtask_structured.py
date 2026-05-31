"""结构稳定的子任务事件解析"""

from __future__ import annotations

from typing import Unpack

import msgspec

from .._json import JsonDict, decode_json_dict
from ..events._base import Event
from ..events.subtask_events import (
    AccountSwitchEvent,
    BattleFormationEvent,
    BattleFormationOperUnavailableEvent,
    BattleFormationSelectedEvent,
    CreditFullOnlyBuyDiscountEvent,
    CustomInfrastRoomGroupsMatchEvent,
    CustomInfrastRoomGroupsMatchFailedEvent,
    CustomInfrastRoomOperatorsEvent,
    DepotEvent,
    DropItem,
    ExceededLimitEvent,
    FacilityEvent,
    FightTimesEvent,
    FinishedEvent,
    InfrastTrainingCompletedEvent,
    InfrastTrainingTimeLeftEvent,
    OperBoxOper,
    OperBoxEvent,
    OwnedOperBoxOper,
    ProcessTaskEvent,
    ProductChangedEvent,
    ProductIncorrectEvent,
    RecruitErrorEvent,
    RecruitNoPermitEvent,
    RecruitOption,
    RecruitResultOper,
    RecruitResultEvent,
    RecruitTagsDetectedEvent,
    RecruitTagsRefreshedEvent,
    RecruitTagsSelectedEvent,
    SSSStageEvent,
    SanityBeforeStageEvent,
    StageDropsEvent,
    StageInfo,
    StageInfoEvent,
    StageQueueMissionCompletedEvent,
    StageQueueStageNotFoundEvent,
    StageQueueUnableToAgentEvent,
    StatItem,
    UnsupportedLevelEvent,
    UserAdditionalOperInvalidEvent,
    UseMedicineEvent,
    CopilotActionEvent,
    CopilotListLoadTaskFileSuccessEvent,
)
from .common import _EventFactory, _SubtaskEventKwargs, _decode_struct
from .payloads import (
    AccountSwitchDetails,
    BattleFormationDetails,
    BattleFormationOperUnavailableDetails,
    BattleFormationSelectedDetails,
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
    InfrastTrainingCompletedDetails,
    InfrastTrainingTimeLeftDetails,
    OperBoxDetails,
    OperBoxOperPayload,
    OwnedOperBoxOperPayload,
    ProcessTaskDetails,
    ProductDetails,
    RecruitErrorDetails,
    RecruitNoPermitDetails,
    RecruitResultOperPayload,
    RecruitResultOptionPayload,
    RecruitResultDetails,
    RecruitSingleTagDetails,
    RecruitTagsDetectedDetails,
    RecruitTagsRefreshedDetails,
    RecruitTagsSelectedDetails,
    SSSStageDetails,
    SanityBeforeStageDetails,
    StageCodeDetails,
    StageDropsDetails,
    StageInfoPayload,
    StageNameDetails,
    StageQueueMissionCompletedDetails,
    StatItemPayload,
    UnsupportedLevelDetails,
    UseMedicineDetails,
    UserAdditionalOperInvalidDetails,
    CopilotActionDetails,
    CopilotListLoadTaskFileSuccessDetails,
)
from .subtask_roguelike import RoguelikeSubtaskParsingMixin


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
    return RecruitResultOper(
        name=item.name,
        id=item.id,
        level=item.level,
    )


def _oper_box_oper_from_payload(item: OperBoxOperPayload) -> OperBoxOper:
    return OperBoxOper(
        id=item.id,
        name=item.name,
        name_en=item.name_en,
        name_jp=item.name_jp,
        name_kr=item.name_kr,
        name_tw=item.name_tw,
        rarity=item.rarity,
        own=item.own,
    )


def _owned_oper_box_oper_from_payload(item: OwnedOperBoxOperPayload) -> OwnedOperBoxOper:
    return OwnedOperBoxOper(
        id=item.id,
        name=item.name,
        own=item.own,
        elite=item.elite,
        level=item.level,
        potential=item.potential,
        rarity=item.rarity,
    )


class StructuredSubtaskParsingMixin(RoguelikeSubtaskParsingMixin):
    """优先走 Struct 解码，只有动态字段才保留手写分支"""

    _subtask_extra_simple_event_classes: dict[str, _EventFactory]

    def _parse_simple_subtask_extra(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        del data
        event_class = self._subtask_extra_simple_event_classes.get(kwargs["what"])
        if event_class is None:
            raise msgspec.ValidationError(f"unsupported simple subtask event: {kwargs['what']}")
        return event_class(**kwargs)

    def _parse_process_task(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), ProcessTaskDetails, "details")
        return ProcessTaskEvent(
            **kwargs,
            task_name=details.task,
            exec_times=details.exec_times,
            max_times=details.max_times,
            action=details.action,
            algorithm=details.algorithm,
        )

    def _parse_stage_drops(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), StageDropsDetails, "details")
        return StageDropsEvent(
            **kwargs,
            drops=[_drop_item_from_payload(item) for item in details.drops],
            stage=StageInfo() if details.stage is None else _stage_info_from_payload(details.stage),
            stars=details.stars,
            stats=[_stat_item_from_payload(item) for item in details.stats],
        )

    def _parse_exceeded_limit(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), ExceededLimitDetails, "details")
        return ExceededLimitEvent(
            **kwargs,
            task_name=details.task,
            exec_times=details.exec_times,
            max_times=details.max_times,
        )

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
        return RecruitResultEvent(
            **kwargs,
            tags=list(details.tags),
            level=details.level,
            result=[_recruit_option_from_payload(item) for item in details.result],
        )

    def _parse_recruit_tags_refreshed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RecruitTagsRefreshedDetails, "details")
        return RecruitTagsRefreshedEvent(
            **kwargs,
            count=details.count,
            refresh_limit=details.refresh_limit,
        )

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
        return FacilityEvent(
            **kwargs,
            facility=details.facility,
            index=details.index,
            product=details.product,
        )

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

    def _parse_credit_full_only_buy_discount(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), CreditFullOnlyBuyDiscountDetails, "details")
        return CreditFullOnlyBuyDiscountEvent(**kwargs, credit=details.credit)

    def _parse_custom_infrast_room_groups_match(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), CustomInfrastRoomGroupsMatchDetails, "details")
        return CustomInfrastRoomGroupsMatchEvent(**kwargs, group=details.group)

    def _parse_custom_infrast_room_groups_match_failed(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), CustomInfrastRoomGroupsMatchFailedDetails, "details")
        return CustomInfrastRoomGroupsMatchFailedEvent(**kwargs, groups=list(details.groups))

    def _parse_custom_infrast_room_operators(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), CustomInfrastRoomOperatorsDetails, "details")
        return CustomInfrastRoomOperatorsEvent(
            **kwargs,
            names=list(details.names),
            candidates=list(details.candidates),
        )

    def _parse_finished(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), FinishedDetails, "details")
        return FinishedEvent(**kwargs, file_name=details.filename)

    def _parse_battle_formation(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), BattleFormationDetails, "details")
        return BattleFormationEvent(**kwargs, formation=list(details.formation))

    def _parse_battle_formation_selected(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), BattleFormationSelectedDetails, "details")
        return BattleFormationSelectedEvent(
            **kwargs,
            selected=details.selected,
            group_name=details.group_name,
        )

    def _parse_battle_formation_oper_unavailable(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), BattleFormationOperUnavailableDetails, "details")
        return BattleFormationOperUnavailableEvent(
            **kwargs,
            oper_name=details.oper_name,
            requirement_type=details.requirement_type,
        )

    def _parse_account_switch(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), AccountSwitchDetails, "details")
        return AccountSwitchEvent(**kwargs, account_name=details.account_name)

    def _parse_copilot_action(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), CopilotActionDetails, "details")
        return CopilotActionEvent(
            **kwargs,
            action=details.action,
            target=details.target,
            doc=details.doc,
            doc_color=details.doc_color,
            elapsed_time=details.elapsed_time,
        )

    def _parse_copilot_list_load_task_file_success(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), CopilotListLoadTaskFileSuccessDetails, "details")
        return CopilotListLoadTaskFileSuccessEvent(
            **kwargs,
            stage_name=details.stage_name,
            file_name=details.file_name,
        )

    def _parse_user_additional_oper_invalid(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), UserAdditionalOperInvalidDetails, "details")
        return UserAdditionalOperInvalidEvent(**kwargs, name=details.name)

    def _parse_sanity_before_stage(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), SanityBeforeStageDetails, "details")
        return SanityBeforeStageEvent(
            **kwargs,
            report_time=details.report_time,
            current_sanity=details.current_sanity,
            max_sanity=details.max_sanity,
        )

    def _parse_fight_times(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), FightTimesDetails, "details")
        return FightTimesEvent(
            **kwargs,
            times_finished=details.times_finished,
            series=details.series,
            sanity_cost=details.sanity_cost,
            finished=details.finished,
        )

    def _parse_use_medicine(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), UseMedicineDetails, "details")
        return UseMedicineEvent(
            **kwargs,
            is_expiring=details.is_expiring,
            count=details.count,
        )

    def _parse_stage_code_event(
        self,
        event_class: _EventFactory,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), StageCodeDetails, "details")
        return event_class(**kwargs, stage_code=details.stage_code)

    def _parse_stage_queue_stage_not_found(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_stage_code_event(StageQueueStageNotFoundEvent, data, **kwargs)

    def _parse_stage_queue_unable_to_agent(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_stage_code_event(StageQueueUnableToAgentEvent, data, **kwargs)

    def _parse_stage_queue_mission_completed(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), StageQueueMissionCompletedDetails, "details")
        return StageQueueMissionCompletedEvent(
            **kwargs,
            stage_code=details.stage_code,
            stars=details.stars,
        )

    def _parse_side_story_reopen_task_not_exists(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        return self._parse_simple_subtask_extra(data, **kwargs)

    def _parse_unsupported_level(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), UnsupportedLevelDetails, "details")
        return UnsupportedLevelEvent(**kwargs, level=details.level)

    def _parse_sss_stage(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), SSSStageDetails, "details")
        return SSSStageEvent(**kwargs, stage=details.stage)

    def _parse_sss_settlement(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_simple_subtask_extra(data, **kwargs)

    def _parse_sss_game_pass(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        return self._parse_simple_subtask_extra(data, **kwargs)

    def _parse_operbox(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), OperBoxDetails, "details")
        return OperBoxEvent(
            **kwargs,
            done=details.done,
            all_opers=[_oper_box_oper_from_payload(item) for item in details.all_opers],
            own_opers=[_owned_oper_box_oper_from_payload(item) for item in details.own_opers],
        )

    def _parse_depot(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), DepotDetails, "details")
        parsed: dict[str, int] = {}
        if details.data:
            parsed = msgspec.convert(decode_json_dict(details.data), type=dict[str, int])

        return DepotEvent(**kwargs, done=details.done, items=parsed)

    def _parse_infrast_training_completed(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), InfrastTrainingCompletedDetails, "details")
        return InfrastTrainingCompletedEvent(
            **kwargs,
            operator=details.operator,
            skill=details.skill,
            level=details.level,
        )

    def _parse_infrast_training_time_left(
        self,
        data: JsonDict,
        **kwargs: Unpack[_SubtaskEventKwargs],
    ) -> Event:
        details = _decode_struct(data.get("details"), InfrastTrainingTimeLeftDetails, "details")
        return InfrastTrainingTimeLeftEvent(
            **kwargs,
            operator=details.operator,
            skill=details.skill,
            level=details.level,
            time=details.time,
        )
