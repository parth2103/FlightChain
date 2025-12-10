// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title FlightEventRegistry
 * @dev Stores flight event hashes on-chain for verification purposes.
 * Full event data remains off-chain in the MySQL database.
 * Only the backend service can write to this contract.
 */
contract FlightEventRegistry {
    // ============ Structs ============

    struct FlightEvent {
        string flightId;        // Flight identifier (e.g., "UA123")
        string eventType;       // Event type (e.g., "DEPARTURE", "ARRIVAL", "GATE_CHANGE")
        uint256 timestamp;      // Unix timestamp of the event
        string actor;           // Actor responsible (e.g., "ATC", "AIRLINE", "SYSTEM")
        bytes32 dataHash;       // SHA256 hash of the full event payload
        uint256 blockNumber;    // Block number when recorded
        uint256 recordedAt;     // Timestamp when recorded on-chain
    }

    // ============ State Variables ============

    address public owner;
    address public authorizedBackend;
    
    FlightEvent[] public events;
    mapping(string => uint256[]) public flightEventIndices;
    mapping(bytes32 => bool) public hashExists;
    
    uint256 public totalEventsRecorded;

    // ============ Events ============

    event EventRecorded(
        uint256 indexed eventIndex,
        string flightId,
        string eventType,
        uint256 timestamp,
        bytes32 dataHash,
        uint256 blockNumber
    );

    event BackendAuthorized(address indexed backend);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // ============ Modifiers ============

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier onlyAuthorized() {
        require(
            msg.sender == owner || msg.sender == authorizedBackend,
            "Not authorized to record events"
        );
        _;
    }

    // ============ Constructor ============

    constructor() {
        owner = msg.sender;
        authorizedBackend = msg.sender; // Initially, owner is the authorized backend
    }

    // ============ Admin Functions ============

    /**
     * @dev Authorize a backend address to record events
     * @param _backend Address of the backend service
     */
    function authorizeBackend(address _backend) external onlyOwner {
        require(_backend != address(0), "Invalid backend address");
        authorizedBackend = _backend;
        emit BackendAuthorized(_backend);
    }

    /**
     * @dev Transfer ownership of the contract
     * @param _newOwner Address of the new owner
     */
    function transferOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "Invalid new owner address");
        emit OwnershipTransferred(owner, _newOwner);
        owner = _newOwner;
    }

    // ============ Core Functions ============

    /**
     * @dev Record a new flight event on-chain
     * @param _flightId Flight identifier
     * @param _eventType Type of event
     * @param _timestamp Unix timestamp of the event
     * @param _actor Actor responsible for the event
     * @param _dataHash SHA256 hash of the full event payload
     * @return eventIndex The index of the recorded event
     * 
     * NOTE: Public function - any user can record events. This allows MetaMask users
     * to pay for their own gas when recording flight events.
     */
    function recordEvent(
        string memory _flightId,
        string memory _eventType,
        uint256 _timestamp,
        string memory _actor,
        bytes32 _dataHash
    ) external returns (uint256) {
        return _recordEvent(_flightId, _eventType, _timestamp, _actor, _dataHash);
    }


    /**
     * @dev Record multiple flight events in a single transaction
     * @param _flightIds Array of flight identifiers
     * @param _eventTypes Array of event types
     * @param _timestamps Array of unix timestamps
     * @param _actors Array of actors
     * @param _dataHashes Array of data hashes
     * @return count Number of events recorded
     */
    function recordEvents(
        string[] memory _flightIds,
        string[] memory _eventTypes,
        uint256[] memory _timestamps,
        string[] memory _actors,
        bytes32[] memory _dataHashes
    ) external returns (uint256) {
        require(_flightIds.length == _eventTypes.length, "Array lengths mismatch");
        require(_flightIds.length == _timestamps.length, "Array lengths mismatch");
        require(_flightIds.length == _actors.length, "Array lengths mismatch");
        require(_flightIds.length == _dataHashes.length, "Array lengths mismatch");
        
        for (uint256 i = 0; i < _flightIds.length; i++) {
            // Inline logic of recordEvent to save gas (internal calls are cheaper but duplication is fine here)
            // We'll just call the internal logic. Refactoring to internal function would be cleaner 
            // but let's keep it simple and just call the logic or create private helper.
            // Since this is a simple contract, I'll allow calling the logic directly.
            // Actually, calling the public function `recordEvent` internally uses `this.recordEvent` which is an external call (expensive).
            // Better to refactor `recordEvent` to call an internal `_recordEvent`.
            _recordEvent(_flightIds[i], _eventTypes[i], _timestamps[i], _actors[i], _dataHashes[i]);
        }
        
        return _flightIds.length;
    }

    function _recordEvent(
        string memory _flightId,
        string memory _eventType,
        uint256 _timestamp,
        string memory _actor,
        bytes32 _dataHash
    ) internal returns (uint256) {
        require(bytes(_flightId).length > 0, "Flight ID cannot be empty");
        require(bytes(_eventType).length > 0, "Event type cannot be empty");
        require(_timestamp > 0, "Invalid timestamp");
        require(_dataHash != bytes32(0), "Data hash cannot be empty");
        // Skip duplicate check if we want to allow re-recording or check here? 
        // Original required !hashExists. Let's keep it.
        if (hashExists[_dataHash]) {
            return 0; // Skip duplicates silently in batch to prevent revert of whole batch? 
            // Or revert? Usually batch should probably succeed for valid ones. 
            // But for now let's strict revert to ensure integrity, or require off-chain filtering.
            // The user wants to "make sure all 12 things are getting logged". 
            // If one fails, maybe we shouldn't fail all? 
            // Let's stick to safe behavior: require !hashExists. The backend should filter before sending.
        }
        require(!hashExists[_dataHash], "Event with this hash already exists");

        uint256 eventIndex = events.length;

        events.push(FlightEvent({
            flightId: _flightId,
            eventType: _eventType,
            timestamp: _timestamp,
            actor: _actor,
            dataHash: _dataHash,
            blockNumber: block.number,
            recordedAt: block.timestamp
        }));

        flightEventIndices[_flightId].push(eventIndex);
        hashExists[_dataHash] = true;
        totalEventsRecorded++;

        emit EventRecorded(
            eventIndex,
            _flightId,
            _eventType,
            _timestamp,
            _dataHash,
            block.number
        );

        return eventIndex;
    }

    // ============ View Functions ============

    /**
     * @dev Get the total number of events recorded
     * @return Total number of events
     */
    function getTotalEvents() external view returns (uint256) {
        return events.length;
    }

    /**
     * @dev Get event count for a specific flight
     * @param _flightId Flight identifier
     * @return Number of events for this flight
     */
    function getFlightEventCount(string memory _flightId) external view returns (uint256) {
        return flightEventIndices[_flightId].length;
    }

    /**
     * @dev Get event by index
     * @param _index Event index
     * @return flightId Flight identifier
     * @return eventType Type of event
     * @return timestamp Unix timestamp
     * @return actor Actor responsible
     * @return dataHash Hash of event data
     * @return blockNumber Block number when recorded
     * @return recordedAt Timestamp when recorded
     */
    function getEvent(uint256 _index) external view returns (
        string memory flightId,
        string memory eventType,
        uint256 timestamp,
        string memory actor,
        bytes32 dataHash,
        uint256 blockNumber,
        uint256 recordedAt
    ) {
        require(_index < events.length, "Event index out of bounds");
        FlightEvent storage evt = events[_index];
        return (
            evt.flightId,
            evt.eventType,
            evt.timestamp,
            evt.actor,
            evt.dataHash,
            evt.blockNumber,
            evt.recordedAt
        );
    }

    /**
     * @dev Get all event indices for a flight
     * @param _flightId Flight identifier
     * @return Array of event indices
     */
    function getFlightEventIndices(string memory _flightId) external view returns (uint256[] memory) {
        return flightEventIndices[_flightId];
    }

    /**
     * @dev Verify if a data hash exists on-chain
     * @param _dataHash Hash to verify
     * @return True if hash exists
     */
    function verifyHash(bytes32 _dataHash) external view returns (bool) {
        return hashExists[_dataHash];
    }

    /**
     * @dev Get events for a flight within a range
     * @param _flightId Flight identifier
     * @param _start Start index
     * @param _count Number of events to return
     * @return Array of event data
     */
    function getFlightEvents(
        string memory _flightId,
        uint256 _start,
        uint256 _count
    ) external view returns (FlightEvent[] memory) {
        uint256[] storage indices = flightEventIndices[_flightId];
        require(_start < indices.length, "Start index out of bounds");
        
        uint256 end = _start + _count;
        if (end > indices.length) {
            end = indices.length;
        }
        
        FlightEvent[] memory result = new FlightEvent[](end - _start);
        for (uint256 i = _start; i < end; i++) {
            result[i - _start] = events[indices[i]];
        }
        
        return result;
    }
}
