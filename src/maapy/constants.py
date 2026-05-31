"""常量定义——消息 ID、任务类型、选项键等。
来源:
  - callback-schema.md (AsstMsg)
  - integration.md (任务类型)
  - AsstCaller.h (选项键类型)
"""

from __future__ import annotations

from enum import IntEnum
from typing import Literal


# ═══ 回调消息 ID ═══


class AsstMsg(IntEnum):
    """回调消息类型。"""

    # 全局消息 (0-9)
    INTERNAL_ERROR = 0
    INIT_FAILED = 1
    CONNECTION_INFO = 2
    ALL_TASKS_COMPLETED = 3
    ASYNC_CALL_INFO = 4
    DESTROYED = 5

    # 任务链消息 (10000-10004)
    TASK_CHAIN_ERROR = 10000
    TASK_CHAIN_START = 10001
    TASK_CHAIN_COMPLETED = 10002
    TASK_CHAIN_EXTRA_INFO = 10003
    TASK_CHAIN_STOPPED = 10004

    # 子任务消息 (20000-20004)
    SUB_TASK_ERROR = 20000
    SUB_TASK_START = 20001
    SUB_TASK_COMPLETED = 20002
    SUB_TASK_EXTRA_INFO = 20003
    SUB_TASK_STOPPED = 20004

    # 上报请求 (30000)
    REPORT_REQUEST = 30000


# ═══ 任务类型 ═══


class AsstTaskType:
    """AsstAppendTask 的 type 参数合法值。"""

    START_UP = "StartUp"
    CLOSE_DOWN = "CloseDown"
    FIGHT = "Fight"
    RECRUIT = "Recruit"
    INFRAST = "Infrast"
    MALL = "Mall"
    AWARD = "Award"
    ROGUELIKE = "Roguelike"
    COPILOT = "Copilot"
    SSS_COPILOT = "SSSCopilot"
    PARADOX_COPILOT = "ParadoxCopilot"
    DEPOT = "Depot"
    OPER_BOX = "OperBox"
    RECLAMATION = "Reclamation"
    CUSTOM = "Custom"
    SINGLE_STEP = "SingleStep"
    VIDEO_RECOGNITION = "VideoRecognition"
    DEBUG = "Debug"


# ═══ 客户端类型 ═══


class ClientType:
    """客户端版本字符串。"""

    OFFICIAL = "Official"
    BILIBILI = "Bilibili"
    TXWY = "txwy"
    YO_STAR_EN = "YoStarEN"
    YO_STAR_JP = "YoStarJP"
    YO_STAR_KR = "YoStarKR"


# ═══ 服务器区服 ═══


class Server:
    CN = "CN"
    US = "US"
    JP = "JP"
    KR = "KR"


# ═══ 静态选项键 ═══


class StaticOptionKey(IntEnum):
    """AsstSetStaticOption 的 key 参数。
    来源: AsstCaller.h
    """

    INVALID = 0
    CPU_OCR = 1
    GPU_OCR = 2


# ═══ 实例选项键 ═══


class InstanceOptionKey(IntEnum):
    """AsstSetInstanceOption 的 key 参数。"""

    INVALID = 0
    TOUCH_MODE = 2
    DEPLOYMENT_WITH_PAUSE = 3
    ADB_LITE_ENABLED = 4
    KILL_ADB_ON_EXIT = 5
    CLIENT_TYPE = 6


# ═══ Win32 窗口绑定选项 ═══


class Win32ScreencapMethod(IntEnum):
    """AsstAttachWindow / AsstAsyncAttachWindow 的截图方式。"""

    NONE = 0
    GDI = 1
    FRAME_POOL = 1 << 1
    DXGI_DESKTOP_DUP = 1 << 2
    DXGI_DESKTOP_DUP_WINDOW = 1 << 3
    PRINT_WINDOW = 1 << 4
    SCREEN_DC = 1 << 5


class Win32InputMethod(IntEnum):
    """AsstAttachWindow / AsstAsyncAttachWindow 的鼠标、键盘输入方式。"""

    NONE = 0
    SEIZE = 1
    SEND_MESSAGE = 1 << 1
    POST_MESSAGE = 1 << 2
    LEGACY_EVENT = 1 << 3
    POST_THREAD_MESSAGE = 1 << 4
    SEND_MESSAGE_WITH_CURSOR_POS = 1 << 5
    POST_MESSAGE_WITH_CURSOR_POS = 1 << 6
    SEND_MESSAGE_WITH_WINDOW_POS = 1 << 7
    POST_MESSAGE_WITH_WINDOW_POS = 1 << 8


# ═══ 基建设施名 ═══


class Facility:
    MFG = "Mfg"
    TRADE = "Trade"
    POWER = "Power"
    CONTROL = "Control"
    RECEPTION = "Reception"
    OFFICE = "Office"
    DORM = "Dorm"
    PROCESSING = "Processing"
    TRAINING = "Training"


# ═══ 基建无人机用途 ═══


class DroneUsage:
    NOT_USE = "_NotUse"
    MONEY = "Money"
    SYNTHETIC_JADE = "SyntheticJade"
    COMBAT_RECORD = "CombatRecord"
    PURE_GOLD = "PureGold"
    ORIGIN_STONE = "OriginStone"
    CHIP = "Chip"


# ═══ ConnectionInfo what 字段 ═══


class ConnectionWhat:
    CONNECTED = "Connected"
    UUID_GOT = "UuidGot"
    CONNECT_FAILED = "ConnectFailed"
    UNSUPPORTED_RESOLUTION = "UnsupportedResolution"
    RESOLUTION_INFO = "ResolutionInfo"
    RESOLUTION_GOT = "ResolutionGot"
    RESOLUTION_ERROR = "ResolutionError"
    RECONNECTING = "Reconnecting"
    RECONNECTED = "Reconnected"
    DISCONNECT = "Disconnect"
    SCREENCAP_FAILED = "ScreencapFailed"
    TOUCH_MODE_NOT_AVAILABLE = "TouchModeNotAvailable"
    FASTEST_WAY_TO_SCREENCAP = "FastestWayToScreencap"
    SCREENCAP_COST = "ScreencapCost"
    UNSUPPORTED_PLAY_TOOLS = "UnsupportedPlayTools"


class AsyncCallWhat:
    CONNECT = "Connect"
    ATTACH_WINDOW = "AttachWindow"
    CLICK = "Click"
    SCREENCAP = "Screencap"
    UNKNOWN = "Unknown"


# ═══ 肉鸽主题 ═══


class RoguelikeTheme:
    PHANTOM = "Phantom"  # 傀影与猩红血钻
    MIZUKI = "Mizuki"  # 水月与深蓝之树
    SAMI = "Sami"  # 探索者的银凇止境
    SARKAZ = "Sarkaz"  # 萨卡兹的无终奇旅
    JIE_GARDEN = "JieGarden"  # 界园志异


# ═══ 生息演算主题 ═══


class ReclamationTheme:
    FIRE = "Fire"  # 沙中之火 (已关闭)
    TALES = "Tales"  # 沙洲遗闻
    RELAUNCH_ANCHOR = "RelaunchAnchor"  # 重铸锚点


# ═══ SubTaskExtraInfo what 字段 ═══


class SubTaskWhat:
    STAGE_DROPS = "StageDrops"
    EXCEEDED_LIMIT = "ExceededLimit"
    RECRUIT_TAGS_DETECTED = "RecruitTagsDetected"
    RECRUIT_SPECIAL_TAG = "RecruitSpecialTag"
    RECRUIT_PRESERVED_TAG = "RecruitPreservedTag"
    RECRUIT_RESULT = "RecruitResult"
    RECRUIT_TAGS_REFRESHED = "RecruitTagsRefreshed"
    RECRUIT_NO_PERMIT = "RecruitNoPermit"
    RECRUIT_TAGS_SELECTED = "RecruitTagsSelected"
    RECRUIT_SLOT_COMPLETED = "RecruitSlotCompleted"
    RECRUIT_ERROR = "RecruitError"
    ENTER_FACILITY = "EnterFacility"
    NOT_ENOUGH_STAFF = "NotEnoughStaff"
    PRODUCT_OF_FACILITY = "ProductOfFacility"
    PRODUCT_INCORRECT = "ProductIncorrect"
    PRODUCT_CHANGED = "ProductChanged"
    PRODUCT_CHANGE_FAIL = "ProductChangeFail"
    CREDIT_FULL_ONLY_BUY_DISCOUNT = "CreditFullOnlyBuyDiscount"
    CUSTOM_INFRAST_ROOM_GROUPS_MATCH = "CustomInfrastRoomGroupsMatch"
    CUSTOM_INFRAST_ROOM_GROUPS_MATCH_FAILED = "CustomInfrastRoomGroupsMatchFailed"
    CUSTOM_INFRAST_ROOM_OPERATORS = "CustomInfrastRoomOperators"
    INFRAST_CONFIRM_BUTTON = "InfrastConfirmButton"
    INFRAST_TRAINING_IDLE = "InfrastTrainingIdle"
    INFRAST_TRAINING_COMPLETED = "InfrastTrainingCompleted"
    INFRAST_TRAINING_TIME_LEFT = "InfrastTrainingTimeLeft"
    BATTLE_FORMATION = "BattleFormation"
    BATTLE_FORMATION_SELECTED = "BattleFormationSelected"
    BATTLE_FORMATION_OPER_UNAVAILABLE = "BattleFormationOperUnavailable"
    BATTLE_FORMATION_PARSE_FAILED = "BattleFormationParseFailed"
    ACCOUNT_SWITCH = "AccountSwitch"
    COPILOT_ACTION = "CopilotAction"
    COPILOT_LIST_LOAD_TASK_FILE_SUCCESS = "CopilotListLoadTaskFileSuccess"
    FINISHED = "Finished"
    MONTHLY_SQUAD_COMPLETED = "MonthlySquadCompleted"
    DEEP_EXPLORATION_COMPLETED = "DeepExplorationCompleted"
    ENCOUNTER_OCR_ERROR = "EncounterOcrError"
    ROGUELIKE_COMBAT_END = "RoguelikeCombatEnd"
    ROGUELIKE_EVENT = "RoguelikeEvent"
    ROGUELIKE_ENCOUNTER_OPTIONS = "RoguelikeEncounterOptions"
    BOSKY_PASSAGE_NODE = "BoskyPassageNode"
    ROGUELIKE_COPPERS_EXCHANGE_INFO = "RoguelikeCoppersExchangeInfo"
    ROGUELIKE_COPPERS_RECOGNITION_ERROR = "RoguelikeCoppersRecognitionError"
    ROGUELIKE_JIE_GARDEN_TARGET_FOUND = "RoguelikeJieGardenTargetFound"
    FOLDARTAL_GAIN_OCR_NEXT_LEVEL = "FoldartalGainOcrNextLevel"
    ROGUELIKE_COLLAPSAL_PARADIGMS = "RoguelikeCollapsalParadigms"
    ROGUELIKE_INVESTMENT = "RoguelikeInvestment"
    ROGUELIKE_INVESTMENT_REACH_LIMIT = "RoguelikeInvestmentReachLimit"
    ROGUELIKE_INVESTMENT_REACH_FULL = "RoguelikeInvestmentReachFull"
    ROGUELIKE_SETTLEMENT = "RoguelikeSettlement"
    SANITY_BEFORE_STAGE = "SanityBeforeStage"
    FIGHT_TIMES = "FightTimes"
    USE_MEDICINE = "UseMedicine"
    STAGE_INFO = "StageInfo"
    STAGE_INFO_ERROR = "StageInfoError"
    STAGE_QUEUE_STAGE_NOT_FOUND = "StageQueueStageNotFound"
    STAGE_QUEUE_UNABLE_TO_AGENT = "StageQueueUnableToAgent"
    STAGE_QUEUE_MISSION_COMPLETED = "StageQueueMissionCompleted"
    SIDE_STORY_REOPEN_TASK_NOT_EXISTS = "SideStoryReopenTaskNotExists"
    PENGUIN_ID = "PenguinId"
    DEPOT = "DepotInfo"
    OPER_BOX = "OperBoxInfo"
    UNSUPPORTED_LEVEL = "UnsupportedLevel"
    SSS_STAGE = "SSSStage"
    SSS_SETTLEMENT = "SSSSettlement"
    SSS_GAME_PASS = "SSSGamePass"


# ═══ 类型别名 (供 Task dataclass 注解使用) ═══
ServerCode = Literal["CN", "US", "JP", "KR"]
ClientCode = Literal["Official", "Bilibili", "txwy", "YoStarEN", "YoStarJP", "YoStarKR"]
FacilityCode = Literal[
    "Mfg",
    "Trade",
    "Power",
    "Control",
    "Reception",
    "Office",
    "Dorm",
    "Processing",
    "Training",
]
DroneCode = Literal[
    "_NotUse",
    "Money",
    "SyntheticJade",
    "CombatRecord",
    "PureGold",
    "OriginStone",
    "Chip",
]
RoguelikeThemeCode = Literal["Phantom", "Mizuki", "Sami", "Sarkaz", "JieGarden"]
ReclamationThemeCode = Literal["Fire", "Tales", "RelaunchAnchor"]
