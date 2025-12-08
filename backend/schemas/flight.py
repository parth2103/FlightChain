"""
Flight Schemas

Pydantic schemas for flight-related API requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from schemas.aircraft import AircraftResponse


class AirlineInfo(BaseModel):
    """Airline information."""
    code: str = Field(..., description="IATA airline code")
    name: str = Field(..., description="Airline name")


class AirportInfo(BaseModel):
    """Airport information."""
    icao: str = Field(..., description="ICAO airport code")
    name: str = Field(..., description="Airport name")


class ScheduleInfo(BaseModel):
    """Schedule information with times."""
    departure: Optional[datetime] = Field(None, description="Departure time")
    arrival: Optional[datetime] = Field(None, description="Arrival time")


class FlightBase(BaseModel):
    """Base flight schema."""
    flight_number: str = Field(..., description="Flight number (e.g., UA123)")
    callsign: Optional[str] = Field(None, description="Flight callsign")


class FlightCreate(FlightBase):
    """Flight creation schema."""
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    origin_icao: Optional[str] = None
    origin_name: Optional[str] = None
    destination_icao: Optional[str] = None
    destination_name: Optional[str] = None
    scheduled_departure: Optional[datetime] = None
    scheduled_arrival: Optional[datetime] = None


class FlightResponse(BaseModel):
    """Full flight response schema."""
    id: int
    flight_number: str
    callsign: Optional[str] = None
    
    airline: Optional[AirlineInfo] = None
    origin: Optional[AirportInfo] = None
    destination: Optional[AirportInfo] = None
    
    scheduled: Optional[ScheduleInfo] = None
    actual: Optional[ScheduleInfo] = None
    
    status: str = "SCHEDULED"
    
    aircraft: Optional[AircraftResponse] = None
    
    departure_delay_minutes: Optional[int] = None
    arrival_delay_minutes: Optional[int] = None
    
    # Data source indicator
    is_mock_data: Optional[bool] = Field(None, description="True if data is synthetic/mock, False if from CSV database")
    data_source: Optional[str] = Field(None, description="Source of flight data: 'csv' or 'mock'")
    
    class Config:
        from_attributes = True


class FlightSearchResponse(BaseModel):
    """Flight search result."""
    found: bool
    flight: Optional[FlightResponse] = None
    message: Optional[str] = None


class FlightSummary(BaseModel):
    """Compact flight summary for display."""
    flight_number: str
    airline_name: Optional[str] = None
    route: str = Field(..., description="Route in format 'ORIGIN → DESTINATION'")
    scheduled_departure: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    status: str
    is_delayed: bool = False
    delay_minutes: Optional[int] = None
