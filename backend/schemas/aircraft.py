"""
Aircraft Schemas

Pydantic schemas for aircraft-related API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class AircraftResponse(BaseModel):
    """Aircraft information response."""
    id: int
    icao24: Optional[str] = Field(None, description="ICAO 24-bit address")
    registration: Optional[str] = Field(None, description="Aircraft registration number")
    
    manufacturer: Optional[str] = Field(None, description="Aircraft manufacturer")
    model: Optional[str] = Field(None, description="Aircraft model")
    type_code: Optional[str] = Field(None, description="Aircraft type code")
    
    serial_number: Optional[str] = Field(None, description="Serial number")
    first_flight_date: Optional[date] = Field(None, description="Date of first flight")
    age_years: Optional[float] = Field(None, description="Age in years")
    
    # Computed
    full_type: Optional[str] = Field(None, description="Full type string (Manufacturer Model)")
    
    class Config:
        from_attributes = True


class AircraftSummary(BaseModel):
    """Compact aircraft summary for display."""
    registration: Optional[str] = None
    type: str = Field(..., description="Aircraft type (e.g., Boeing 737-800)")
    age_years: Optional[float] = None
    
    @property
    def age_display(self) -> str:
        """Format age for display."""
        if self.age_years is None:
            return "Unknown"
        return f"{self.age_years:.1f} years"
