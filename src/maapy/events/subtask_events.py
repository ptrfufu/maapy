"""子任务回调事件"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._base import Event, SubTaskMixin


@dataclass(slots=True, frozen=True)
class RecruitResultOper:
    name: str = ""
    id: str = ""
    level: int = 0


@dataclass(slots=True, frozen=True)
class OperBoxOper:
    id: str = ""
    name: str = ""
    name_en: str = ""
    name_jp: str = ""
    name_kr: str = ""
    name_tw: str = ""
    rarity: int = 0
    own: bool = False


@dataclass(slots=True, frozen=True)
class OwnedOperBoxOper:
    id: str = ""
    name: str = ""
    own: bool = False
    elite: int = 0
    level: int = 0
    potential: int = 0
    rarity: int = 0


@dataclass(slots=True, frozen=True)
class DropItem:
    item_id: str = ""
    item_name: str = ""
    quantity: int = 0


@dataclass(slots=True, frozen=True)
class StageInfo:
    stage_code: str = ""
    stage_id: str = ""


@dataclass(slots=True, frozen=True)
class StatItem:
    item_id: str = ""
    item_name: str = ""
    quantity: int = 0
    add_quantity: int = 0


@dataclass(slots=True, frozen=True)
class RecruitOption:
    tags: list[str] = field(default_factory=list)
    level: int = 0
    opers: list[RecruitResultOper] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class SubTaskErrorEvent(Event, SubTaskMixin):
    """msg=20000"""

    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class SubTaskStartedEvent(Event, SubTaskMixin):
    """msg=20001"""

    task_name: str = ""
    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class SubTaskCompletedEvent(Event, SubTaskMixin):
    """msg=20002"""

    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class SubTaskStoppedEvent(Event, SubTaskMixin):
    """msg=20004"""

    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class SubTaskExtraInfoEvent(Event, SubTaskMixin):
    """msg=20003"""

    what: str = ""
    why: str = ""


@dataclass(slots=True, frozen=True)
class MatchDeploymentStartedEvent(SubTaskStartedEvent):
    """实验录像识别中的部署匹配开始"""


@dataclass(slots=True, frozen=True)
class MatchDeploymentCompletedEvent(SubTaskCompletedEvent):
    """实验录像识别中的部署匹配完成"""


@dataclass(slots=True, frozen=True)
class MatchDeploymentErrorEvent(SubTaskErrorEvent):
    """实验录像识别中的部署匹配失败"""


@dataclass(slots=True, frozen=True)
class SliceStartedEvent(SubTaskStartedEvent):
    """实验录像识别中的切片分析开始"""


@dataclass(slots=True, frozen=True)
class SliceCompletedEvent(SubTaskCompletedEvent):
    """实验录像识别中的切片分析完成"""


@dataclass(slots=True, frozen=True)
class SliceErrorEvent(SubTaskErrorEvent):
    """实验录像识别中的切片分析失败"""


@dataclass(slots=True, frozen=True)
class CompSkillStartedEvent(SubTaskStartedEvent):
    """实验录像识别中的技能比对开始"""


@dataclass(slots=True, frozen=True)
class CompSkillCompletedEvent(SubTaskCompletedEvent):
    """实验录像识别中的技能比对完成"""


@dataclass(slots=True, frozen=True)
class CompSkillErrorEvent(SubTaskErrorEvent):
    """实验录像识别中的技能比对失败"""


@dataclass(slots=True, frozen=True)
class DetectOperatorsStartedEvent(SubTaskStartedEvent):
    """实验录像识别中的场上干员检测开始"""


@dataclass(slots=True, frozen=True)
class DetectOperatorsCompletedEvent(SubTaskCompletedEvent):
    """实验录像识别中的场上干员检测完成"""


@dataclass(slots=True, frozen=True)
class DetectOperatorsErrorEvent(SubTaskErrorEvent):
    """实验录像识别中的场上干员检测失败"""


@dataclass(slots=True, frozen=True)
class ClassifyDirectionStartedEvent(SubTaskStartedEvent):
    """实验录像识别中的朝向分类开始"""


@dataclass(slots=True, frozen=True)
class ClassifyDirectionCompletedEvent(SubTaskCompletedEvent):
    """实验录像识别中的朝向分类完成"""


@dataclass(slots=True, frozen=True)
class ClassifyDirectionErrorEvent(SubTaskErrorEvent):
    """实验录像识别中的朝向分类失败"""


@dataclass(slots=True, frozen=True)
class ProcessTaskEvent(SubTaskExtraInfoEvent):
    """通用流程子任务"""

    task_name: str = ""
    exec_times: int = 0
    max_times: int = 0
    action: str = ""
    algorithm: str = ""


@dataclass(slots=True, frozen=True)
class ExceededLimitEvent(SubTaskExtraInfoEvent):
    """流程任务达到执行次数上限"""

    task_name: str = ""
    exec_times: int = 0
    max_times: int = 0


@dataclass(slots=True, frozen=True)
class StageDropsEvent(SubTaskExtraInfoEvent):
    """关卡掉落信息"""

    drops: list[DropItem] = field(default_factory=list)
    stage: StageInfo | None = None
    stars: int = 0
    stats: list[StatItem] = field(default_factory=list)

    def get_accumulated(self, item_id: str) -> int:
        for item in self.stats:
            if item.item_id == item_id:
                return item.quantity
        return 0


@dataclass(slots=True, frozen=True)
class StageInfoEvent(SubTaskExtraInfoEvent):
    """关卡信息"""

    name: str = ""


@dataclass(slots=True, frozen=True)
class StageInfoErrorEvent(SubTaskExtraInfoEvent):
    """关卡识别失败"""


@dataclass(slots=True, frozen=True)
class RecruitTagsDetectedEvent(SubTaskExtraInfoEvent):
    """公招标签识别结果"""

    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RecruitResultEvent(SubTaskExtraInfoEvent):
    """公招结果"""

    tags: list[str] = field(default_factory=list)
    level: int = 0
    result: list[RecruitOption] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RecruitTagsRefreshedEvent(SubTaskExtraInfoEvent):
    """公招标签刷新进度"""

    count: int = 0
    refresh_limit: int = 3


@dataclass(slots=True, frozen=True)
class RecruitTagsSelectedEvent(SubTaskExtraInfoEvent):
    """公招已选标签"""

    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RecruitNoPermitEvent(SubTaskExtraInfoEvent):
    """公招没有招聘许可"""

    continue_refresh: bool = False


@dataclass(slots=True, frozen=True)
class RecruitErrorEvent(SubTaskErrorEvent):
    """公招流程错误"""

    refresh_limit: int | None = None


@dataclass(slots=True, frozen=True)
class FacilityEvent(SubTaskExtraInfoEvent):
    """基建设施信息"""

    facility: str = ""
    index: int = 0
    product: str | None = None


@dataclass(slots=True, frozen=True)
class ProductEvent(SubTaskExtraInfoEvent):
    """基建产物信息"""

    product: str = ""


@dataclass(slots=True, frozen=True)
class ProductIncorrectEvent(ProductEvent):
    """产物与配置不一致"""


@dataclass(slots=True, frozen=True)
class ProductChangedEvent(ProductEvent):
    """产物已切换"""


@dataclass(slots=True, frozen=True)
class ProductChangeFailEvent(SubTaskExtraInfoEvent):
    """产物切换失败"""


@dataclass(slots=True, frozen=True)
class CreditFullOnlyBuyDiscountEvent(SubTaskExtraInfoEvent):
    """仅买折扣时信用点溢出提醒"""

    credit: int = 0


@dataclass(slots=True, frozen=True)
class OperBoxEvent(SubTaskExtraInfoEvent):
    """干员识别结果"""

    done: bool = False
    all_opers: list[OperBoxOper] = field(default_factory=list)
    own_opers: list[OwnedOperBoxOper] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class DepotEvent(SubTaskExtraInfoEvent):
    """仓库识别结果"""

    done: bool = False
    items: dict[str, int] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class CustomInfrastRoomGroupsMatchEvent(SubTaskExtraInfoEvent):
    """自定义基建房间命中的分组"""

    group: str = ""


@dataclass(slots=True, frozen=True)
class CustomInfrastRoomGroupsMatchFailedEvent(SubTaskExtraInfoEvent):
    """自定义基建房间分组全部匹配失败"""

    groups: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class CustomInfrastRoomOperatorsEvent(SubTaskExtraInfoEvent):
    """自定义基建房间目标干员配置"""

    names: list[str] = field(default_factory=list)
    candidates: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class InfrastConfirmButtonEvent(SubTaskExtraInfoEvent):
    """基建宿舍确认按钮弹出"""


@dataclass(slots=True, frozen=True)
class InfrastTrainingIdleEvent(SubTaskExtraInfoEvent):
    """训练室当前空闲"""


@dataclass(slots=True, frozen=True)
class InfrastTrainingCompletedEvent(SubTaskExtraInfoEvent):
    """训练室技能升级完成"""

    operator: str = ""
    skill: str = ""
    level: int = 0


@dataclass(slots=True, frozen=True)
class InfrastTrainingTimeLeftEvent(SubTaskExtraInfoEvent):
    """训练室剩余时间"""

    operator: str = ""
    skill: str = ""
    level: int = 0
    time: str = ""


@dataclass(slots=True, frozen=True)
class BattleFormationEvent(SubTaskExtraInfoEvent):
    """编队解析结果"""

    formation: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class BattleFormationSelectedEvent(SubTaskExtraInfoEvent):
    """编队已选中的干员或分组"""

    selected: str = ""
    group_name: str = ""


@dataclass(slots=True, frozen=True)
class BattleFormationOperUnavailableEvent(SubTaskExtraInfoEvent):
    """编队中某个干员不满足要求"""

    oper_name: str = ""
    requirement_type: str = ""


@dataclass(slots=True, frozen=True)
class BattleFormationParseFailedEvent(SubTaskExtraInfoEvent):
    """编队配置解析失败"""


@dataclass(slots=True, frozen=True)
class AccountSwitchEvent(SubTaskExtraInfoEvent):
    """账号切换结果"""

    account_name: str = ""


@dataclass(slots=True, frozen=True)
class CopilotActionEvent(SubTaskExtraInfoEvent):
    """共战脚本当前执行动作"""

    action: str = ""
    target: str = ""
    doc: str = ""
    doc_color: str = ""
    elapsed_time: int = 0


@dataclass(slots=True, frozen=True)
class CopilotListLoadTaskFileSuccessEvent(SubTaskExtraInfoEvent):
    """作业文件加载成功"""

    stage_name: str = ""
    file_name: str = ""


@dataclass(slots=True, frozen=True)
class UserAdditionalOperInvalidEvent(SubTaskErrorEvent):
    """用户追加干员配置非法"""

    name: str = ""


@dataclass(slots=True, frozen=True)
class FinishedEvent(SubTaskExtraInfoEvent):
    """实验识别任务已输出结果文件"""

    file_name: str = ""


@dataclass(slots=True, frozen=True)
class MonthlySquadCompletedEvent(SubTaskExtraInfoEvent):
    """月度小队完成"""


@dataclass(slots=True, frozen=True)
class DeepExplorationCompletedEvent(SubTaskExtraInfoEvent):
    """深入调查完成"""


@dataclass(slots=True, frozen=True)
class EncounterOcrErrorEvent(SubTaskExtraInfoEvent):
    """肉鸽事件名识别失败"""


@dataclass(slots=True, frozen=True)
class RoguelikeCombatEndEvent(SubTaskExtraInfoEvent):
    """肉鸽战斗结束"""


@dataclass(slots=True, frozen=True)
class RoguelikeEventInfoEvent(SubTaskExtraInfoEvent):
    """肉鸽事件识别与选择结果"""

    name: str = ""
    default_choose: int = 0
    choose_option: int = 0


@dataclass(slots=True, frozen=True)
class RoguelikeEncounterOption:
    enabled: bool = False
    text: str = ""


@dataclass(slots=True, frozen=True)
class RoguelikeEncounterOptionsEvent(SubTaskExtraInfoEvent):
    """肉鸽事件选项列表"""

    options: list[RoguelikeEncounterOption] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class BoskyPassageNodeEvent(SubTaskExtraInfoEvent):
    """界园树洞当前节点类型"""

    node_type: str = ""


@dataclass(slots=True, frozen=True)
class RoguelikeCoppersRecognitionErrorEvent(SubTaskExtraInfoEvent):
    """界园通宝识别失败"""

    recognized_name: str = ""


@dataclass(slots=True, frozen=True)
class RoguelikeCoppersExchangeInfoEvent(SubTaskExtraInfoEvent):
    """界园通宝替换信息"""

    to_discard: str = ""
    to_pickup: str = ""


@dataclass(slots=True, frozen=True)
class RoguelikeJieGardenTargetFoundEvent(SubTaskExtraInfoEvent):
    """界园已命中目标常乐节点"""

    target_subtype: str = ""


@dataclass(slots=True, frozen=True)
class FoldartalGainOcrNextLevelEvent(SubTaskExtraInfoEvent):
    """萨米预见识别结果"""

    foldartal: str = ""


@dataclass(slots=True, frozen=True)
class RoguelikeCollapsalParadigmsEvent(SubTaskExtraInfoEvent):
    """萨米坍缩范式变化"""

    cur: str = ""
    deepen_or_weaken: int = 0
    prev: str = ""


@dataclass(slots=True, frozen=True)
class RoguelikeInvestmentEvent(SubTaskExtraInfoEvent):
    """肉鸽投资进度"""

    count: int = 0
    total: int = 0
    deposit: int = -1


@dataclass(slots=True, frozen=True)
class RoguelikeInvestmentReachLimitEvent(SubTaskExtraInfoEvent):
    """肉鸽投资达到设定上限"""

    limit: int = 0


@dataclass(slots=True, frozen=True)
class RoguelikeInvestmentReachFullEvent(SubTaskExtraInfoEvent):
    """肉鸽投资达到存款上限"""


@dataclass(slots=True, frozen=True)
class RoguelikeSettlementEvent(SubTaskExtraInfoEvent):
    """肉鸽结算信息"""

    game_pass: bool = False
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


@dataclass(slots=True, frozen=True)
class SanityBeforeStageEvent(SubTaskExtraInfoEvent):
    """进入关卡前理智信息"""

    report_time: str = ""
    current_sanity: int | None = None
    max_sanity: int | None = None


@dataclass(slots=True, frozen=True)
class FightTimesEvent(SubTaskExtraInfoEvent):
    """战斗次数信息"""

    times_finished: int | None = None
    series: int | None = None
    sanity_cost: int | None = None
    finished: bool | None = None


@dataclass(slots=True, frozen=True)
class UseMedicineEvent(SubTaskExtraInfoEvent):
    """使用理智药"""

    is_expiring: bool = False
    count: int = 0


@dataclass(slots=True, frozen=True)
class StageCodeEvent(SubTaskExtraInfoEvent):
    """带关卡编号的事件"""

    stage_code: str = ""


@dataclass(slots=True, frozen=True)
class StageQueueStageNotFoundEvent(StageCodeEvent):
    """队列关卡不存在"""


@dataclass(slots=True, frozen=True)
class StageQueueUnableToAgentEvent(StageCodeEvent):
    """队列关卡无法代理"""


@dataclass(slots=True, frozen=True)
class StageQueueMissionCompletedEvent(StageCodeEvent):
    """队列关卡已完成"""

    stars: int = 0


@dataclass(slots=True, frozen=True)
class SideStoryReopenTaskNotExistsEvent(SubTaskExtraInfoEvent):
    """复刻任务不存在"""


@dataclass(slots=True, frozen=True)
class UnsupportedLevelEvent(SubTaskExtraInfoEvent):
    """不支持的关卡"""

    level: str = ""


@dataclass(slots=True, frozen=True)
class SSSStageEvent(SubTaskExtraInfoEvent):
    """保全当前关卡"""

    stage: str = ""


@dataclass(slots=True, frozen=True)
class SSSSettlementEvent(SubTaskExtraInfoEvent):
    """保全结算"""


@dataclass(slots=True, frozen=True)
class SSSGamePassEvent(SubTaskExtraInfoEvent):
    """保全通关"""
