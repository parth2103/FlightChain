"""
Blockchain Router

API endpoints for blockchain verification and event exploration.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas.blockchain import (
    BlockchainEventResponse,
    BlockchainVerification,
    BlockchainStats,
    PreparedTransaction,
    FlightEventFromChain,
)
from pydantic import BaseModel
from datetime import datetime
from services.blockchain_service import BlockchainService
from services.flight_service import FlightService
from config import settings

router = APIRouter()


@router.get(
    "/flight/{flight_id}/blockchain-events",
    response_model=list[BlockchainEventResponse],
    summary="Get blockchain event log",
    description="Get all blockchain-verified events for a flight."
)
async def get_blockchain_events(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """
    Get blockchain event log for a flight.
    
    Returns all events that have been recorded on the blockchain,
    including transaction hashes and block numbers.
    """
    # Check if flight exists
    service = FlightService(db)
    flight = service.get_flight_by_id(flight_id)
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    blockchain_service = BlockchainService(db)
    return blockchain_service.get_flight_blockchain_events(flight_id)


@router.get(
    "/blockchain/verify/{data_hash}",
    response_model=BlockchainVerification,
    summary="Verify data hash",
    description="Verify if a data hash exists on the blockchain."
)
async def verify_hash(
    data_hash: str,
    db: Session = Depends(get_db)
):
    """
    Verify that a data hash exists on the blockchain.
    
    This can be used to independently verify that event data
    has not been tampered with.
    """
    blockchain_service = BlockchainService(db)
    return await blockchain_service.verify_hash(data_hash)


@router.get(
    "/blockchain/stats",
    response_model=BlockchainStats,
    summary="Get blockchain statistics",
    description="Get statistics about the blockchain contract."
)
async def get_blockchain_stats(
    db: Session = Depends(get_db)
):
    """
    Get blockchain statistics.
    
    Returns total events recorded, contract address, and other stats.
    """
    blockchain_service = BlockchainService(db)
    return await blockchain_service.get_stats()


@router.post(
    "/blockchain/record-event/{event_id}",
    summary="Record event on blockchain",
    description="Manually trigger blockchain recording for an event."
)
async def record_event_on_blockchain(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Record an event on the blockchain.
    
    This is typically called automatically when events are created,
    but can be triggered manually if needed.
    """
    blockchain_service = BlockchainService(db)
    result = await blockchain_service.record_event(event_id)
    
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to record event on blockchain"
        )
    
    return {
        "success": True,
        "tx_hash": result.tx_hash,
        "block_number": result.block_number
    }


@router.get(
    "/blockchain/prepare-transaction/{event_id}",
    response_model=PreparedTransaction,
    summary="Prepare transaction for MetaMask",
    description="Prepare a transaction to record an event on blockchain. Returns transaction data that can be sent via MetaMask."
)
async def prepare_transaction(
    event_id: int,
    db: Session = Depends(get_db)
):
    """
    Prepare a transaction to record an event on blockchain.
    
    This endpoint prepares the transaction data without executing it.
    The frontend will use this data to prompt MetaMask for user approval.
    """
    from models.event import FlightEvent
    from config import settings
    
    event = db.query(FlightEvent).filter(FlightEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if contract address is configured
    if not settings.contract_address:
        raise HTTPException(
            status_code=500,
            detail="Contract address not configured. Please deploy the contract and set CONTRACT_ADDRESS in backend .env"
        )
    
    blockchain_service = BlockchainService(db)
    
    # Check connection first
    if not blockchain_service.is_connected():
        raise HTTPException(
            status_code=500,
            detail=f"Cannot connect to blockchain at {settings.ganache_url}. Make sure Ganache is running on port 7545."
        )
    
    if not blockchain_service.contract:
        raise HTTPException(
            status_code=500,
            detail=f"Contract not initialized. Contract address: {settings.contract_address or 'NOT SET'}. Check CONTRACT_ADDRESS in backend .env file."
        )
    
    try:
        transaction = await blockchain_service.prepare_record_event_transaction(event_id)
        if not transaction:
            raise HTTPException(
                status_code=500,
                detail="Failed to prepare transaction: No transaction data returned."
            )
        return transaction
    except Exception as e:
        error_detail = str(e)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare transaction: {error_detail}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to prepare transaction: {error_detail}"
        )


class BatchTransactionRequest(BaseModel):
    event_ids: list[int]


@router.post(
    "/blockchain/prepare-batch-transaction",
    response_model=PreparedTransaction,
    summary="Prepare batch transaction",
    description="Prepare a single transaction to record multiple events."
)
async def prepare_batch_transaction(
    request: BatchTransactionRequest,
    db: Session = Depends(get_db)
):
    """
    Prepare a batch transaction.
    """
    from models.event import FlightEvent
    from config import settings
    
    # Check checks...
    if not settings.contract_address:
         raise HTTPException(status_code=500, detail="Contract address not configured")
         
    blockchain_service = BlockchainService(db)
    
    if not blockchain_service.is_connected():
        raise HTTPException(status_code=500, detail="Cannot connect to blockchain")
        
    try:
        transaction = await blockchain_service.prepare_batch_transaction(request.event_ids)
        if not transaction:
             raise HTTPException(status_code=500, detail="Failed to prepare transaction")
        return transaction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/blockchain/flight-events/{flight_number}",
    response_model=list[FlightEventFromChain],
    summary="Get flight events from blockchain",
    description="Read flight events directly from the blockchain contract."
)
async def get_flight_events_from_chain(
    flight_number: str,
    db: Session = Depends(get_db)
):
    """
    Get flight events directly from blockchain.
    
    This reads events directly from the smart contract, bypassing the database.
    Useful for verifying data integrity.
    """
    blockchain_service = BlockchainService(db)
    events = await blockchain_service.read_flight_events_from_chain(flight_number.upper())
    return events


class TransactionConfirmation(BaseModel):
    """Transaction confirmation from frontend."""
    event_id: int
    tx_hash: str
    block_number: Optional[int] = None


@router.post(
    "/blockchain/confirm-transaction",
    summary="Confirm transaction from MetaMask",
    description="Record a confirmed transaction hash after MetaMask sends it to blockchain."
)
async def confirm_transaction(
    confirmation: TransactionConfirmation,
    db: Session = Depends(get_db)
):
    """
    Record a confirmed blockchain transaction.
    
    Called by the frontend after MetaMask successfully sends a transaction.
    Updates the blockchain_records table with the transaction details.
    """
    from models.event import FlightEvent
    from models.blockchain_record import BlockchainRecord
    
    event = db.query(FlightEvent).filter(FlightEvent.id == confirmation.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if record already exists
    existing = db.query(BlockchainRecord).filter(BlockchainRecord.event_id == confirmation.event_id).first()
    if existing:
        # Update existing record
        existing.tx_hash = confirmation.tx_hash
        existing.block_number = confirmation.block_number
        existing.status = "confirmed"
        existing.confirmed_at = datetime.now()
    else:
        # Create new record
        blockchain_service = BlockchainService(db)
        record = BlockchainRecord(
            event_id=confirmation.event_id,
            tx_hash=confirmation.tx_hash,
            block_number=confirmation.block_number,
            contract_address=settings.contract_address,
            data_hash=event.data_hash,
            status="confirmed",
            confirmed_at=datetime.now()
        )
        db.add(record)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Transaction confirmed and recorded"
    }
