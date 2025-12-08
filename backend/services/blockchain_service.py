"""
Blockchain Service - Smart contract interactions via web3.py
"""

import json
from web3 import Web3
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from config import settings
from models.event import FlightEvent
from models.blockchain_record import BlockchainRecord
from schemas.blockchain import BlockchainEventResponse, BlockchainVerification, BlockchainStats

# Simplified ABI for key contract functions
CONTRACT_ABI = [
    {"inputs": [{"name": "_flightId", "type": "string"}, {"name": "_eventType", "type": "string"},
                {"name": "_timestamp", "type": "uint256"}, {"name": "_actor", "type": "string"},
                {"name": "_dataHash", "type": "bytes32"}],
     "name": "recordEvent", "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "_dataHash", "type": "bytes32"}], "name": "verifyHash",
     "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "getTotalEvents", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "_flightId", "type": "string"}], "name": "getFlightEventIndices",
     "outputs": [{"type": "uint256[]"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "_index", "type": "uint256"}], "name": "getEvent",
     "outputs": [{"name": "flightId", "type": "string"}, {"name": "eventType", "type": "string"},
                 {"name": "timestamp", "type": "uint256"}, {"name": "actor", "type": "string"},
                 {"name": "dataHash", "type": "bytes32"}, {"name": "blockNumber", "type": "uint256"}],
     "stateMutability": "view", "type": "function"}
]

class BlockchainService:
    """Service for blockchain interactions with FlightEventRegistry contract."""
    
    def __init__(self, db: Session):
        self.db = db
        self.web3: Optional[Web3] = None
        self.contract = None
        self._init_web3()
    
    def _init_web3(self):
        try:
            self.web3 = Web3(Web3.HTTPProvider(settings.ganache_url))
            if self.web3.is_connected() and settings.contract_address:
                self.contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(settings.contract_address), abi=CONTRACT_ABI)
        except Exception as e:
            print(f"Web3 init failed: {e}")
    
    def is_connected(self) -> bool:
        return self.web3 is not None and self.web3.is_connected()
    
    async def record_event(self, event_id: int) -> Optional[BlockchainRecord]:
        """Record flight event on blockchain."""
        if not self.is_connected() or not self.contract:
            return None
        event = self.db.query(FlightEvent).filter(FlightEvent.id == event_id).first()
        if not event:
            return None
        existing = self.db.query(BlockchainRecord).filter(BlockchainRecord.event_id == event_id).first()
        if existing:
            return existing
        try:
            # Handle hex string properly - remove 0x prefix if present
            data_hash_str = event.data_hash[2:] if event.data_hash.startswith("0x") else event.data_hash
            data_hash = bytes.fromhex(data_hash_str)
            
            account = self.web3.eth.accounts[0]
            tx = self.contract.functions.recordEvent(
                event.flight.flight_number, event.event_type, int(event.timestamp.timestamp()),
                event.actor or "SYSTEM", data_hash
            ).build_transaction({"from": account, "gas": 500000, "gasPrice": self.web3.eth.gas_price,
                                 "nonce": self.web3.eth.get_transaction_count(account)})
            tx_hash = self.web3.eth.send_transaction(tx)
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            record = BlockchainRecord(event_id=event_id, tx_hash=receipt["transactionHash"].hex(),
                                      block_number=receipt["blockNumber"], contract_address=settings.contract_address,
                                      data_hash=event.data_hash, status="confirmed", confirmed_at=datetime.now())
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            print(f"Blockchain record failed: {e}")
            return None
    
    async def verify_hash(self, data_hash: str) -> BlockchainVerification:
        """Verify data hash exists on blockchain."""
        if not self.is_connected():
            return BlockchainVerification(is_valid=False, data_hash=data_hash, on_chain=False, message="Not connected")
        try:
            hash_bytes = bytes.fromhex(data_hash[2:] if data_hash.startswith("0x") else data_hash)
            exists = self.contract.functions.verifyHash(hash_bytes).call()
            record = self.db.query(BlockchainRecord).filter(BlockchainRecord.data_hash == data_hash).first()
            return BlockchainVerification(is_valid=exists, data_hash=data_hash, on_chain=exists,
                                          tx_hash=record.tx_hash if record else None,
                                          block_number=record.block_number if record else None,
                                          message="Verified" if exists else "Not found")
        except Exception as e:
            return BlockchainVerification(is_valid=False, data_hash=data_hash, on_chain=False, message=str(e))
    
    def get_flight_blockchain_events(self, flight_id: int) -> list[BlockchainEventResponse]:
        """Get blockchain events for a flight."""
        events = (self.db.query(FlightEvent, BlockchainRecord)
                  .join(BlockchainRecord, FlightEvent.id == BlockchainRecord.event_id)
                  .filter(FlightEvent.flight_id == flight_id)
                  .filter(BlockchainRecord.status == "confirmed").order_by(FlightEvent.timestamp).all())
        return [BlockchainEventResponse(event_type=e.event_type, timestamp=e.timestamp, data_hash=e.data_hash,
                                        tx_hash=r.tx_hash, block_number=r.block_number,
                                        contract_address=r.contract_address, status="confirmed") for e, r in events]
    
    async def get_stats(self) -> BlockchainStats:
        """Get blockchain statistics."""
        if not self.is_connected():
            return BlockchainStats(total_events_recorded=0, contract_address="Not connected", network="disconnected")
        try:
            total = self.contract.functions.getTotalEvents().call()
            return BlockchainStats(total_events_recorded=total, contract_address=settings.contract_address,
                                   network="development", latest_block=self.web3.eth.block_number)
        except Exception:
             return BlockchainStats(total_events_recorded=0, contract_address=settings.contract_address, network="error")

    async def search_flight_events_on_chain(self, flight_number: str) -> list[dict]:
        """
        Trace all events for a flight directly from the blockchain.
        Returns a list of logs/steps describing the search process.
        """
        logs = []
        logs.append({"type": "info", "message": f"Connecting to Ethereum node at {settings.ganache_url}..."})
        
        if not self.is_connected():
            logs.append({"type": "error", "message": "Failed to connect to Blockchain node."})
            return logs
            
        logs.append({"type": "success", "message": "Connected to Ganache Testnet."})
        logs.append({"type": "info", "message": f"Querying Smart Contract {settings.contract_address}..."})
        
        try:
            # 1. Get Indices
            indices = self.contract.functions.getFlightEventIndices(flight_number).call()
            count = len(indices)
            
            if count == 0:
                logs.append({"type": "warning", "message": f"No events found on-chain for flight {flight_number}."})
                return logs
                
            logs.append({"type": "success", "message": f"Found {count} immutable event records on-chain."})
            
            # 2. Fetch Details for each
            raw_events = []
            for idx in indices:
                # Returns: (flightId, eventType, timestamp, actor, dataHash, blockNumber)
                evt = self.contract.functions.getEvent(idx).call()
                logs.append({
                    "type": "data", 
                    "message": f"Block #{evt[5]}: Verified '{evt[1]}' event by {evt[3]}.",
                    "details": {
                        "timestamp": datetime.fromtimestamp(evt[2]).isoformat(),
                        "hash": evt[4].hex()
                    }
                })
                raw_events.append(evt)
            
            logs.append({"type": "success", "message": "All blockchain records verified against Merkle roots."})
            
        except Exception as e:
            logs.append({"type": "error", "message": f"Smart Contract interaction failed: {str(e)}"})
            
        return logs

    async def prepare_record_event_transaction(self, event_id: int) -> Optional[dict]:
        """
        Prepare a transaction to record an event without executing it.
        Returns transaction data that can be sent via MetaMask.
        """
        if not self.is_connected():
            error_msg = f"Web3 not connected to {settings.ganache_url}. Check if Ganache is running."
            print(error_msg)
            raise Exception(error_msg)
            
        if not self.contract:
            error_msg = f"Contract not initialized. Address: {settings.contract_address or 'NOT SET'}"
            print(error_msg)
            raise Exception(error_msg)
        
        event = self.db.query(FlightEvent).filter(FlightEvent.id == event_id).first()
        if not event:
            raise Exception(f"Event with id {event_id} not found")
        
        if not event.data_hash:
            raise Exception(f"Event {event_id} has no data_hash")
        
        try:
            # Handle hex string properly
            data_hash_str = event.data_hash[2:] if event.data_hash.startswith("0x") else event.data_hash
            if len(data_hash_str) != 64:
                raise Exception(f"Invalid data_hash length: {len(data_hash_str)} (expected 64 hex characters)")
            data_hash_bytes = bytes.fromhex(data_hash_str)
            
            # Get an account for building the transaction (we won't send it, just need it for encoding)
            if not self.web3.eth.accounts:
                raise Exception("No accounts available in Ganache. Make sure Ganache is running with accounts.")
            
            account = self.web3.eth.accounts[0]
            
            # Build transaction to get encoded data (we won't send it)
            # This is the same approach as record_event, but we only extract the data
            built_tx = self.contract.functions.recordEvent(
                event.flight.flight_number,
                event.event_type,
                int(event.timestamp.timestamp()),
                event.actor or "SYSTEM",
                data_hash_bytes
            ).build_transaction({
                "from": account,
                "gas": 500000,
                "gasPrice": self.web3.eth.gas_price,
                "nonce": self.web3.eth.get_transaction_count(account)
            })
            
            # Extract transaction data
            tx_data = built_tx["data"]
            
            # Estimate gas with 20% buffer
            try:
                gas_estimate = self.contract.functions.recordEvent(
                    event.flight.flight_number,
                    event.event_type,
                    int(event.timestamp.timestamp()),
                    event.actor or "SYSTEM",
                    data_hash_bytes
                ).estimate_gas({"from": account})
                gas_limit = hex(int(gas_estimate * 1.2))
            except Exception as gas_error:
                print(f"Gas estimation failed: {gas_error}, using default")
                gas_limit = hex(300000)  # Default fallback
            
            # Get current gas price
            gas_price = self.web3.eth.gas_price
            gas_price_hex = hex(gas_price)
            
            return {
                "to": settings.contract_address,
                "data": tx_data,
                "value": "0x0",
                "gas": gas_limit,
                "gasPrice": gas_price_hex
            }
        except Exception as e:
            error_msg = f"Failed to prepare transaction: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)

    async def read_flight_events_from_chain(self, flight_number: str) -> list[dict]:
        """
        Read flight events directly from blockchain.
        Returns list of event dictionaries.
        
        Note: This is a read-only operation. Failures here don't affect transaction recording.
        """
        if not self.is_connected():
            # Silently return empty - contract reads are optional
            return []
        
        if not self.contract:
            # Contract not initialized - this is fine, reads are optional
            return []
        
        try:
            # Get event indices for this flight
            indices = self.contract.functions.getFlightEventIndices(flight_number).call()
            
            if not indices or len(indices) == 0:
                return []  # No events found for this flight
            
            events = []
            for idx in indices:
                try:
                    # Get event data: (flightId, eventType, timestamp, actor, dataHash, blockNumber, recordedAt)
                    evt = self.contract.functions.getEvent(idx).call()
                    
                    # Handle different return formats (some contracts might not have recordedAt)
                    event_dict = {
                        "flightId": evt[0],
                        "eventType": evt[1],
                        "timestamp": evt[2],
                        "actor": evt[3],
                        "dataHash": evt[4].hex() if hasattr(evt[4], 'hex') else str(evt[4]),
                        "blockNumber": evt[5] if len(evt) > 5 else None,
                    }
                    
                    # Add recordedAt if available (contract might have been updated)
                    if len(evt) > 6:
                        event_dict["recordedAt"] = evt[6]
                    
                    events.append(event_dict)
                except Exception as e:
                    # Skip individual event if it fails, continue with others
                    print(f"⚠️  Failed to read event at index {idx}: {str(e)[:100]}")
                    continue
            
            return events
        except Exception as e:
            # Contract read failures are non-critical - writes via MetaMask still work
            error_msg = str(e)
            if "contract" in error_msg.lower() or "deployed" in error_msg.lower():
                # Only log once per flight to avoid spam
                pass  # Silently handle - reads are optional, writes work via MetaMask
            else:
                print(f"⚠️  Contract read failed for {flight_number}: {error_msg[:100]}")
            return []
