"""
Delay Analysis Schemas

Pydantic schemas for delay analysis API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class DelayCategory(str, Enum):
    """Delay severity categories."""
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SIGNIFICANT = "SIGNIFICANT"
    SEVERE = "SEVERE"


class DelayType(str, Enum):
    """Types of delays."""
    DEPARTURE_DELAY = "DEPARTURE_DELAY"
    ARRIVAL_DELAY = "ARRIVAL_DELAY"
    GATE_DELAY = "GATE_DELAY"
    TAXI_DELAY = "TAXI_DELAY"
    AIRBORNE_DELAY = "AIRBORNE_DELAY"
    WEATHER_DELAY = "WEATHER_DELAY"
    ATC_DELAY = "ATC_DELAY"
    MECHANICAL_DELAY = "MECHANICAL_DELAY"
    CREW_DELAY = "CREW_DELAY"
    CONNECTING_DELAY = "CONNECTING_DELAY"


class DelayReason(BaseModel):
    """Individual delay reason."""
    type: DelayType = Field(..., description="Type of delay")
    minutes: float = Field(..., description="Duration in minutes")
    explanation: str = Field(..., description="Human-readable explanation")
    confidence: Optional[float] = Field(None, description="Confidence score 0-1")


class DelayAnalysisResponse(BaseModel):
    """Complete delay analysis for a flight."""
    flight_id: int
    flight_number: str
    
    # Summary
    is_delayed: bool = Field(..., description="Whether flight is considered delayed")
    total_delay_minutes: float = Field(..., description="Total delay in minutes")
    category: DelayCategory = Field(..., description="Delay severity category")
    
    # Breakdown
    departure_delay_minutes: Optional[float] = Field(None, description="Departure delay")
    arrival_delay_minutes: Optional[float] = Field(None, description="Arrival delay")
    
    # Reasons
    reasons: list[DelayReason] = Field(default_factory=list, description="Identified delay reasons")
    
    # Human-readable
    human_readable: str = Field(..., description="Plain English explanation")
    
    # On-time thresholds used
    on_time_threshold_minutes: int = Field(15, description="Minutes considered on-time")


def categorize_delay(minutes: float) -> DelayCategory:
    """Categorize delay by minutes."""
    if minutes <= 0:
        return DelayCategory.NONE
    elif minutes <= 15:
        return DelayCategory.MINOR
    elif minutes <= 30:
        return DelayCategory.MODERATE
    elif minutes <= 60:
        return DelayCategory.SIGNIFICANT
    else:
        return DelayCategory.SEVERE
