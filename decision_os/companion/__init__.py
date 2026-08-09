"""Private localhost companion for one bounded Decision OS Run."""

from .continuation import (
    ContinuationError,
    ContinuationIntegrityError,
    StageBContinuationRequest,
)
from .controller import CompanionController, ContinuationStateError
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
    "ContinuationError",
    "ContinuationIntegrityError",
    "ContinuationStateError",
    "ContractFact",
    "DecisionRoute",
    "SupervisorContext",
    "SupervisorGate",
    "SupervisorJudgment",
    "StageBContinuationRequest",
    "judge_continuation",
]
__version__ = "0.1.0"
