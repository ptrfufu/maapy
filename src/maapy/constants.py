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
    """回调消息类型。
    来源: docs.maa.plus/zh-cn/protocol/callback-schema.html
    """

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
    """AsstAppendTask 的 type 参数合法值。
    来源: docs.maa.plus/zh-cn/protocol/integration.html
    """

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
    TOUCH_TYPE = 2
    DEPLOYMENT_WITH_PAUSE = 3
    ADB_LITE_ENABLED = 4
    KILL_ON_ADB_EXIT = 5


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
    RESOLUTION_ERROR = "ResolutionError"
    RECONNECTING = "Reconnecting"
    RECONNECTED = "Reconnected"
    DISCONNECT = "Disconnect"
    SCREENCAP_FAILED = "ScreencapFailed"
    TOUCH_MODE_NOT_AVAILABLE = "TouchModeNotAvailable"


# ═══ 肉鸽主题 ═══

class RoguelikeTheme:
    PHANTOM = "Phantom"       # 傀影与猩红血钻
    MIZUKI = "Mizuki"          # 水月与深蓝之树
    SAMI = "Sami"              # 探索者的银凇止境
    SARKAZ = "Sarkaz"          # 萨卡兹的无终奇旅
    JIE_GARDEN = "JieGarden"   # 界园志异


# ═══ 生息演算主题 ═══

class ReclamationTheme:
    FIRE = "Fire"                      # 沙中之火 (已关闭)
    TALES = "Tales"                    # 沙洲遗闻
    RELAUNCH_ANCHOR = "RelaunchAnchor" # 重铸锚点


# ═══ SubTaskExtraInfo what 字段 ═══

class SubTaskWhat:
    STAGE_DROPS = "StageDrops"
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
    STAGE_INFO = "StageInfo"
    STAGE_INFO_ERROR = "StageInfoError"
    PENGUIN_ID = "PenguinId"
    DEPOT = "DepotInfo"
    OPER_BOX = "OperBoxInfo"
    UNSUPPORTED_LEVEL = "UnsupportedLevel"


# ═══ 类型别名 (供 Task dataclass 注解使用) ═══
ServerCode = Literal["CN", "US", "JP", "KR"]
ClientCode = Literal["Official", "Bilibili", "txwy", "YoStarEN", "YoStarJP", "YoStarKR"]
FacilityCode = Literal[
    "Mfg", "Trade", "Power", "Control", "Reception",
    "Office", "Dorm", "Processing", "Training",
]
DroneCode = Literal[
    "_NotUse", "Money", "SyntheticJade", "CombatRecord",
    "PureGold", "OriginStone", "Chip",
]
RoguelikeThemeCode = Literal["Phantom", "Mizuki", "Sami", "Sarkaz", "JieGarden"]
ReclamationThemeCode = Literal["Fire", "Tales", "RelaunchAnchor"]
