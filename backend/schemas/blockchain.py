"""
Blockchain Schemas

Pydantic schemas for blockchain-related API responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BlockchainRecordResponse(BaseModel):
    """Blockchain record response schema."""
    id: int
    event_id: int
    tx_hash: str
    block_number: Optional[int] = None
    contract_address: Optional[str] = None
    event_index: Optional[int] = None
    data_hash: Optional[str] = None
    status: str = "pending"
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BlockchainEventResponse(BaseModel):
    """Blockchain event for explorer display."""
    event_type: str = Field(..., description="Type of flight event")
    timestamp: datetime = Field(..., description="Event timestamp")
    data_hash: str = Field(..., description="SHA256 hash of event data")
    tx_hash: str = Field(..., description="Blockchain transaction hash")
    block_number: Optional[int] = Field(None, description="Block number")
    contract_address: Optional[str] = Field(None, description="Smart contract address")
    status: str = Field("confirmed", description="Verification status")


class BlockchainVerification(BaseModel):
    """Result of verifying a hash on blockchain."""
    is_valid: bool = Field(..., description="Whether the hash exists on-chain")
    data_hash: str = Field(..., description="The hash that was verified")
    on_chain: bool = Field(..., description="Whether found on blockchain")
    tx_hash: Optional[str] = Field(None, description="Original transaction hash")
    block_number: Optional[int] = Field(None, description="Block number")
    message: str = Field(..., description="Human-readable verification result")


class BlockchainStats(BaseModel):
    """Blockchain statistics."""
    total_events_recorded: int = Field(..., description="Total events on-chain")
    contract_address: str = Field(..., description="Smart contract address")
    network: str = Field("development", description="Network name")
    latest_block: Optional[int] = Field(None, description="Latest block number")


class PreparedTransaction(BaseModel):
    """Prepared transaction for MetaMask."""
    to: str = Field(..., description="Contract address")
    data: str = Field(..., description="Encoded function call data")
    value: str = Field("0x0", description="Value to send (in wei)")
    gas: Optional[str] = Field(None, description="Estimated gas limit")
    gasPrice: Optional[str] = Field(None, description="Gas price")


class FlightEventFromChain(BaseModel):
    """Flight event read directly from blockchain."""
    flightId: str
    eventType: str
    timestamp: int
    actor: str
    dataHash: str
    blockNumber: int
    recordedAt: int
