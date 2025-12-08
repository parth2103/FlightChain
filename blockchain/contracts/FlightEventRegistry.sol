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
        require(bytes(_flightId).length > 0, "Flight ID cannot be empty");
        require(bytes(_eventType).length > 0, "Event type cannot be empty");
        require(_timestamp > 0, "Invalid timestamp");
        require(_dataHash != bytes32(0), "Data hash cannot be empty");
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
