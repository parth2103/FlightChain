"""
Flight Event Model

SQLAlchemy model for flight events.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class FlightEvent(Base):
    """Flight event database model."""
    
    __tablename__ = "flight_events"

    id = Column(Integer, primary_key=True, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    actor = Column(String(100))
    
    # Payload stored as JSON
    payload = Column(JSON)
    
    # Hash of the payload for blockchain verification
    data_hash = Column(String(66))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    flight = relationship("Flight", back_populates="events")
    blockchain_record = relationship("BlockchainRecord", back_populates="event", uselist=False)
    
    def __repr__(self):
        return f"<FlightEvent {self.event_type} @ {self.timestamp}>"
    
    @property
    def is_verified(self) -> bool:
        """Check if this event has been verified on blockchain."""
        return self.blockchain_record is not None and self.blockchain_record.status == "confirmed"


# Event type constants
class EventTypes:
    """Standard flight event types."""
    
    SCHEDULED = "SCHEDULED"
    GATE_ASSIGNED = "GATE_ASSIGNED"
    CHECK_IN_OPEN = "CHECK_IN_OPEN"
    CHECK_IN_CLOSED = "CHECK_IN_CLOSED"
    BOARDING_OPEN = "BOARDING_OPEN"
    BOARDING_CLOSED = "BOARDING_CLOSED"
    PUSHBACK = "PUSHBACK"
    TAXI_OUT = "TAXI_OUT"
    TAKEOFF = "TAKEOFF"
    AIRBORNE = "AIRBORNE"
    CRUISE = "CRUISE"
    DESCENT = "DESCENT"
    APPROACH = "APPROACH"
    LANDING = "LANDING"
    TAXI_IN = "TAXI_IN"
    ARRIVAL = "ARRIVAL"
    GATE_ARRIVAL = "GATE_ARRIVAL"
    DELAY_ANNOUNCED = "DELAY_ANNOUNCED"
    GATE_CHANGE = "GATE_CHANGE"
    CANCELLED = "CANCELLED"
    DIVERTED = "DIVERTED"


# Actor constants
class Actors:
    """Standard event actors."""
    
    SYSTEM = "SYSTEM"
    AIRLINE = "AIRLINE"
    ATC = "ATC"
    AIRPORT = "AIRPORT"
    GATE_AGENT = "GATE_AGENT"
    PILOT = "PILOT"
    GROUND_CREW = "GROUND_CREW"
    WEATHER = "WEATHER"
