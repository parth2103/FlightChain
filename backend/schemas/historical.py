"""
Historical Stats Schemas

Pydantic schemas for historical baseline API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class HistoricalBaselineResponse(BaseModel):
    """Historical performance baseline for a route."""
    route_key: str = Field(..., description="Route key (ORIG-DEST)")
    airline_code: Optional[str] = Field(None, description="Airline code")
    
    # Statistics
    avg_delay_minutes: Optional[float] = Field(None, description="Average delay in minutes")
    on_time_percentage: Optional[float] = Field(None, description="On-time percentage")
    total_flights: Optional[int] = Field(None, description="Total flights in sample")
    
    # Delay breakdown
    avg_departure_delay: Optional[float] = Field(None, description="Avg departure delay")
    avg_arrival_delay: Optional[float] = Field(None, description="Avg arrival delay")
    
    # Sample period
    sample_period_start: Optional[date] = Field(None, description="Start of sample period")
    sample_period_end: Optional[date] = Field(None, description="End of sample period")
    
    # Categories
    delay_category: Optional[str] = Field(None, description="Delay category rating")
    on_time_category: Optional[str] = Field(None, description="On-time performance rating")
    
    class Config:
        from_attributes = True


class HistoricalComparison(BaseModel):
    """Comparison of current flight to historical baseline."""
    current_delay_minutes: Optional[float] = None
    avg_delay_minutes: Optional[float] = None
    
    is_better_than_average: Optional[bool] = None
    difference_minutes: Optional[float] = None
    
    percentile: Optional[float] = Field(None, description="Where this flight ranks (0-100)")
    
    message: str = Field(..., description="Human-readable comparison")


class RoutePerformanceChart(BaseModel):
    """Data for route performance visualization."""
    route_key: str
    
    # Chart data points
    labels: list[str] = Field(default_factory=list, description="Time period labels")
    on_time_data: list[float] = Field(default_factory=list, description="On-time percentages")
    delay_data: list[float] = Field(default_factory=list, description="Average delays")
    
    # Summary
    trend: str = Field("stable", description="Performance trend: improving, declining, stable")
