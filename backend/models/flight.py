"""
Flight Model

SQLAlchemy model for flight information.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Flight(Base):
    """Flight database model."""
    
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String(10), nullable=False, index=True)
    callsign = Column(String(10), index=True)
    
    # Airline info
    airline_code = Column(String(3))
    airline_name = Column(String(100))
    
    # Route info
    origin_icao = Column(String(4))
    origin_name = Column(String(100))
    destination_icao = Column(String(4))
    destination_name = Column(String(100))
    
    # Times
    scheduled_departure = Column(DateTime)
    actual_departure = Column(DateTime)
    scheduled_arrival = Column(DateTime)
    actual_arrival = Column(DateTime)
    
    # Status
    status = Column(String(20), default="SCHEDULED")
    
    # Aircraft relationship
    aircraft_id = Column(Integer, ForeignKey("aircraft.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    aircraft = relationship("Aircraft", back_populates="flights")
    events = relationship("FlightEvent", back_populates="flight", order_by="FlightEvent.timestamp")
    
    def __repr__(self):
        return f"<Flight {self.flight_number} ({self.origin_icao} -> {self.destination_icao})>"
    
    @property
    def departure_delay_minutes(self) -> int | None:
        """Calculate departure delay in minutes."""
        if self.actual_departure and self.scheduled_departure:
            delta = self.actual_departure - self.scheduled_departure
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def arrival_delay_minutes(self) -> int | None:
        """Calculate arrival delay in minutes."""
        if self.actual_arrival and self.scheduled_arrival:
            delta = self.actual_arrival - self.scheduled_arrival
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def route_key(self) -> str:
        """Get route key for historical lookups."""
        return f"{self.origin_icao}-{self.destination_icao}"
