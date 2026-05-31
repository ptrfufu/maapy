"""肉鸽相关子任务回调解析"""

from __future__ import annotations

from typing import Unpack

from .._json import JsonDict
from ..events._base import Event
from ..events.subtask_events import (
    BoskyPassageNodeEvent,
    DeepExplorationCompletedEvent,
    EncounterOcrErrorEvent,
    FoldartalGainOcrNextLevelEvent,
    MonthlySquadCompletedEvent,
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
)
from .common import _SubtaskEventKwargs, _decode_struct
from .payloads import (
    BoskyPassageNodeDetails,
    FoldartalGainOcrNextLevelDetails,
    RoguelikeCollapsalParadigmsDetails,
    RoguelikeCoppersExchangeInfoDetails,
    RoguelikeCoppersRecognitionErrorDetails,
    RoguelikeEncounterOptionsDetails,
    RoguelikeEventDetails,
    RoguelikeInvestmentDetails,
    RoguelikeInvestmentReachLimitDetails,
    RoguelikeJieGardenTargetFoundDetails,
    RoguelikeSettlementDetails,
)


class RoguelikeSubtaskParsingMixin:
    """集中处理肉鸽事件，稳定 payload 一律走 msgspec.Struct 解码"""

    def _parse_monthly_squad_completed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        del data
        return MonthlySquadCompletedEvent(**kwargs)

    def _parse_deep_exploration_completed(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        del data
        return DeepExplorationCompletedEvent(**kwargs)

    def _parse_encounter_ocr_error(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        del data
        return EncounterOcrErrorEvent(**kwargs)

    def _parse_roguelike_combat_end(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        del data
        return RoguelikeCombatEndEvent(**kwargs)

    def _parse_roguelike_event(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeEventDetails, "details")
        return RoguelikeEventInfoEvent(
            **kwargs,
            name=details.name,
            default_choose=details.default_choose,
            choose_option=details.choose_option,
        )

    def _parse_roguelike_encounter_options(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeEncounterOptionsDetails, "details")
        return RoguelikeEncounterOptionsEvent(
            **kwargs,
            options=[
                RoguelikeEncounterOption(enabled=item.enabled, text=item.text)
                for item in details.options
            ],
        )

    def _parse_bosky_passage_node(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), BoskyPassageNodeDetails, "details")
        return BoskyPassageNodeEvent(**kwargs, node_type=details.node_type)

    def _parse_roguelike_coppers_exchange_info(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeCoppersExchangeInfoDetails, "details")
        return RoguelikeCoppersExchangeInfoEvent(
            **kwargs,
            to_discard=details.to_discard,
            to_pickup=details.to_pickup,
        )

    def _parse_roguelike_coppers_recognition_error(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeCoppersRecognitionErrorDetails, "details")
        return RoguelikeCoppersRecognitionErrorEvent(**kwargs, recognized_name=details.recognized_name)

    def _parse_roguelike_jie_garden_target_found(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeJieGardenTargetFoundDetails, "details")
        return RoguelikeJieGardenTargetFoundEvent(**kwargs, target_subtype=details.target_subtype)

    def _parse_foldartal_gain_ocr_next_level(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), FoldartalGainOcrNextLevelDetails, "details")
        return FoldartalGainOcrNextLevelEvent(**kwargs, foldartal=details.foldartal)

    def _parse_roguelike_collapsal_paradigms(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeCollapsalParadigmsDetails, "details")
        return RoguelikeCollapsalParadigmsEvent(
            **kwargs,
            cur=details.cur,
            deepen_or_weaken=details.deepen_or_weaken,
            prev=details.prev,
        )

    def _parse_roguelike_investment(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeInvestmentDetails, "details")
        return RoguelikeInvestmentEvent(
            **kwargs,
            count=details.count,
            total=details.total,
            deposit=details.deposit,
        )

    def _parse_roguelike_investment_reach_limit(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeInvestmentReachLimitDetails, "details")
        return RoguelikeInvestmentReachLimitEvent(**kwargs, limit=details.limit)

    def _parse_roguelike_investment_reach_full(
        self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]
    ) -> Event:
        del data
        return RoguelikeInvestmentReachFullEvent(**kwargs)

    def _parse_roguelike_settlement(self, data: JsonDict, **kwargs: Unpack[_SubtaskEventKwargs]) -> Event:
        details = _decode_struct(data.get("details"), RoguelikeSettlementDetails, "details")
        return RoguelikeSettlementEvent(
            **kwargs,
            game_pass=details.game_pass,
            floor=details.floor,
            step=details.step,
            combat=details.combat,
            recruit=details.recruit,
            collection=details.collection,
            boss=details.boss,
            emergency=details.emergency,
            difficulty=details.difficulty,
            score=details.score,
            exp=details.exp,
            skill=details.skill,
        )
