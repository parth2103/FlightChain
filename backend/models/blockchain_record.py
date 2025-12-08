"""
Blockchain Record Model

SQLAlchemy model for blockchain transaction records.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class BlockchainRecord(Base):
    """Blockchain record database model."""
    
    __tablename__ = "blockchain_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("flight_events.id"), nullable=False, index=True)
    
    # Transaction details
    tx_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer)
    contract_address = Column(String(42))
    event_index = Column(Integer)  # Index in the smart contract events array
    
    # Hash verification
    data_hash = Column(String(66))
    
    # Status
    status = Column(String(20), default="pending")  # pending, confirmed, failed
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    confirmed_at = Column(DateTime)
    
    # Relationships
    event = relationship("FlightEvent", back_populates="blockchain_record")
    
    def __repr__(self):
        return f"<BlockchainRecord tx={self.tx_hash[:10]}... block={self.block_number}>"
    
    @property
    def is_confirmed(self) -> bool:
        """Check if transaction is confirmed."""
        return self.status == "confirmed"
    
    @property
    def explorer_url(self) -> str:
        """Get blockchain explorer URL (for mainnet, would point to Etherscan)."""
        # For development, just return a local reference
        return f"#tx/{self.tx_hash}"
