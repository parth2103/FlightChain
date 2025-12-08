"""
Historical Stats Model

SQLAlchemy model for historical flight performance statistics.
"""

from sqlalchemy import Column, Integer, String, Date, Numeric
from sqlalchemy.sql import func
from database import Base


class HistoricalStats(Base):
    """Historical statistics database model."""
    
    __tablename__ = "historical_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    # Route identification
    route_key = Column(String(9), nullable=False, index=True)  # Format: ORIG-DEST
    airline_code = Column(String(3), index=True)
    
    # Statistics
    avg_delay_minutes = Column(Numeric(6, 2))
    on_time_percentage = Column(Numeric(5, 2))
    total_flights = Column(Integer)
    
    # Delay breakdown
    avg_departure_delay = Column(Numeric(6, 2))
    avg_arrival_delay = Column(Numeric(6, 2))
    
    # Sample period
    sample_period_start = Column(Date)
    sample_period_end = Column(Date)
    
    # Timestamps
    created_at = Column(Date, server_default=func.now())
    
    def __repr__(self):
        return f"<HistoricalStats {self.route_key} ({self.airline_code})>"
    
    @property
    def delay_category(self) -> str:
        """Categorize average delay."""
        if self.avg_delay_minutes is None:
            return "UNKNOWN"
        delay = float(self.avg_delay_minutes)
        if delay <= 5:
            return "EXCELLENT"
        elif delay <= 15:
            return "GOOD"
        elif delay <= 30:
            return "FAIR"
        else:
            return "POOR"
    
    @property
    def on_time_category(self) -> str:
        """Categorize on-time performance."""
        if self.on_time_percentage is None:
            return "UNKNOWN"
        pct = float(self.on_time_percentage)
        if pct >= 90:
            return "EXCELLENT"
        elif pct >= 80:
            return "GOOD"
        elif pct >= 70:
            return "FAIR"
        else:
            return "POOR"
