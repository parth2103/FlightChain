"""
Event Schemas

Pydantic schemas for flight event API requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


class EventBase(BaseModel):
    """Base event schema."""
    event_type: str = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="When the event occurred")
    actor: Optional[str] = Field(None, description="Actor responsible for the event")


class EventCreate(EventBase):
    """Event creation schema."""
    flight_id: int
    payload: Optional[dict[str, Any]] = None


class EventResponse(BaseModel):
    """Event response schema."""
    id: int
    flight_id: int
    event_type: str
    timestamp: datetime
    actor: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    data_hash: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BlockchainVerificationInfo(BaseModel):
    """Blockchain verification info for an event."""
    is_verified: bool = False
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    verified_at: Optional[datetime] = None


class EventWithVerification(BaseModel):
    """Event with blockchain verification status."""
    id: int
    event_type: str
    timestamp: datetime
    actor: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    data_hash: Optional[str] = None
    
    # Blockchain verification
    blockchain: BlockchainVerificationInfo
    
    class Config:
        from_attributes = True


class EventTimelineItem(BaseModel):
    """Event formatted for timeline display."""
    event_type: str
    timestamp: datetime
    actor: Optional[str] = None
    description: str = Field(..., description="Human-readable event description")
    is_verified: bool = False
    tx_hash: Optional[str] = None
    
    # UI hints
    icon: Optional[str] = None
    color: Optional[str] = None
