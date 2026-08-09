"""Private localhost companion for one bounded Decision OS Run."""

from .controller import CompanionController
from .server import CompanionServer
from .supervisor import (
    ContractFact,
    DecisionRoute,
    SupervisorContext,
    SupervisorGate,
    SupervisorJudgment,
    judge_continuation,
)

__all__ = [
    "CompanionController",
    "CompanionServer",
    "ContractFact",
    "DecisionRoute",
    "SupervisorContext",
    "SupervisorGate",
    "SupervisorJudgment",
    "judge_continuation",
]
__version__ = "0.1.0"
