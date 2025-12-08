"""
Aircraft Model

SQLAlchemy model for aircraft information.
"""

from sqlalchemy import Column, Integer, String, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import date


class Aircraft(Base):
    """Aircraft database model."""
    
    __tablename__ = "aircraft"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identification
    icao24 = Column(String(6), unique=True, index=True)
    registration = Column(String(10))
    
    # Type info
    manufacturer = Column(String(100))
    model = Column(String(100))
    type_code = Column(String(4))
    
    # Details
    serial_number = Column(String(50))
    first_flight_date = Column(Date)
    
    # Computed age (stored for query performance)
    age_years = Column(Numeric(4, 1))
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    
    # Relationships
    flights = relationship("Flight", back_populates="aircraft")
    
    def __repr__(self):
        return f"<Aircraft {self.registration} ({self.manufacturer} {self.model})>"
    
    @property
    def calculated_age(self) -> float | None:
        """Calculate age from first flight date."""
        if self.first_flight_date:
            delta = date.today() - self.first_flight_date
            return round(delta.days / 365.25, 1)
        return None
    
    @property
    def full_type(self) -> str:
        """Get full aircraft type string."""
        parts = []
        if self.manufacturer:
            parts.append(self.manufacturer)
        if self.model:
            parts.append(self.model)
        return " ".join(parts) if parts else "Unknown"
