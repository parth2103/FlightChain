"""FlightChain Schemas Package"""

from schemas.flight import (
    FlightBase,
    FlightCreate,
    FlightResponse,
    FlightSearchResponse,
    FlightSummary,
)
from schemas.event import (
    EventBase,
    EventCreate,
    EventResponse,
    EventWithVerification,
)
from schemas.blockchain import (
    BlockchainRecordResponse,
    BlockchainEventResponse,
    BlockchainVerification,
)
from schemas.delay import (
    DelayReason,
    DelayAnalysisResponse,
)
from schemas.aircraft import (
    AircraftResponse,
)
from schemas.historical import (
    HistoricalBaselineResponse,
)

__all__ = [
    # Flight
    "FlightBase",
    "FlightCreate",
    "FlightResponse",
    "FlightSearchResponse",
    "FlightSummary",
    # Event
    "EventBase",
    "EventCreate",
    "EventResponse",
    "EventWithVerification",
    # Blockchain
    "BlockchainRecordResponse",
    "BlockchainEventResponse",
    "BlockchainVerification",
    # Delay
    "DelayReason",
    "DelayAnalysisResponse",
    # Aircraft
    "AircraftResponse",
    # Historical
    "HistoricalBaselineResponse",
]
