"""
Event Assembler Service

Service for assembling and managing flight events.
"""

import hashlib
import json
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from models.event import FlightEvent
from models.blockchain_record import BlockchainRecord
from schemas.event import EventWithVerification, BlockchainVerificationInfo


class EventAssembler:
    """Service for assembling flight events."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_events_for_flight(self, flight_id: int) -> list[FlightEvent]:
        """Get all events for a flight ordered by timestamp."""
        return (
            self.db.query(FlightEvent)
            .filter(FlightEvent.flight_id == flight_id)
            .order_by(FlightEvent.timestamp)
            .all()
        )
    
    def get_events_with_verification(self, flight_id: int) -> list[EventWithVerification]:
        """Get events with blockchain verification status."""
        events = self.get_events_for_flight(flight_id)
        
        result = []
        for event in events:
            # Get blockchain record if exists
            blockchain_record = (
                self.db.query(BlockchainRecord)
                .filter(BlockchainRecord.event_id == event.id)
                .first()
            )
            
            verification = BlockchainVerificationInfo(
                is_verified=blockchain_record is not None and blockchain_record.status == "confirmed",
                tx_hash=blockchain_record.tx_hash if blockchain_record else None,
                block_number=blockchain_record.block_number if blockchain_record else None,
                verified_at=blockchain_record.confirmed_at if blockchain_record else None,
            )
            
            result.append(EventWithVerification(
                id=event.id,
                event_type=event.event_type,
                timestamp=event.timestamp,
                actor=event.actor,
                payload=event.payload,
                data_hash=event.data_hash,
                blockchain=verification,
            ))
        
        return result
    
    def create_event(
        self,
        flight_id: int,
        event_type: str,
        timestamp: datetime,
        actor: Optional[str] = None,
        payload: Optional[dict] = None
    ) -> FlightEvent:
        """
        Create a new flight event.
        
        Automatically generates a data hash for blockchain recording.
        """
        # Calculate data hash
        data_hash = self._calculate_hash(flight_id, event_type, timestamp, actor, payload)
        
        event = FlightEvent(
            flight_id=flight_id,
            event_type=event_type,
            timestamp=timestamp,
            actor=actor,
            payload=payload,
            data_hash=data_hash,
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        return event
    
    def create_events_from_states(
        self,
        flight_id: int,
        states: list[dict]
    ) -> list[FlightEvent]:
        """
        Create events from a list of state changes.
        
        Used to convert OpenSky state vectors into discrete events.
        """
        events = []
        
        for state in states:
            event_type = state.get("event_type", "STATE_UPDATE")
            timestamp = state.get("timestamp", datetime.now())
            actor = state.get("actor", "SYSTEM")
            payload = state.get("payload", {})
            
            event = self.create_event(
                flight_id=flight_id,
                event_type=event_type,
                timestamp=timestamp,
                actor=actor,
                payload=payload
            )
            events.append(event)
        
        return events
    
    def _calculate_hash(
        self,
        flight_id: int,
        event_type: str,
        timestamp: datetime,
        actor: Optional[str],
        payload: Optional[dict]
    ) -> str:
        """Calculate SHA256 hash of event data."""
        data = {
            "flight_id": flight_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "actor": actor,
            "payload": payload,
        }
        
        # Create deterministic JSON string
        json_str = json.dumps(data, sort_keys=True, default=str)
        
        # Calculate hash
        hash_bytes = hashlib.sha256(json_str.encode()).digest()
        return "0x" + hash_bytes.hex()


# Event type to description mapping
EVENT_DESCRIPTIONS = {
    "SCHEDULED": "Flight scheduled",
    "GATE_ASSIGNED": "Gate assigned",
    "CHECK_IN_OPEN": "Check-in opened",
    "CHECK_IN_CLOSED": "Check-in closed",
    "BOARDING_OPEN": "Boarding commenced",
    "BOARDING_CLOSED": "Boarding completed",
    "PUSHBACK": "Aircraft pushback initiated",
    "TAXI_OUT": "Taxiing to runway",
    "TAKEOFF": "Aircraft departed",
    "AIRBORNE": "Aircraft airborne",
    "CRUISE": "Aircraft at cruising altitude",
    "DESCENT": "Beginning descent",
    "APPROACH": "On final approach",
    "LANDING": "Aircraft landed",
    "TAXI_IN": "Taxiing to gate",
    "ARRIVAL": "Arrived at destination",
    "GATE_ARRIVAL": "Arrived at gate",
    "DELAY_ANNOUNCED": "Delay announced",
    "GATE_CHANGE": "Gate changed",
    "CANCELLED": "Flight cancelled",
    "DIVERTED": "Flight diverted",
}


def get_event_description(event_type: str) -> str:
    """Get human-readable description for event type."""
    return EVENT_DESCRIPTIONS.get(event_type, event_type.replace("_", " ").title())
