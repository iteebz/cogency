from enum import Enum

class NodeName(str, Enum):
    MEMORIZE = "memorize"
    SELECT_TOOLS = "select_tools"
    THINK = "think"
    PLAN = "plan"
    ACT = "act"
    REFLECT = "reflect"
    RESPOND = "respond"
