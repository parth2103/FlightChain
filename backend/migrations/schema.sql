-- Database Schema for FlightChain

SET FOREIGN_KEY_CHECKS = 0;

-- 1. Aircraft Table
CREATE TABLE IF NOT EXISTS aircraft (
    id INT AUTO_INCREMENT PRIMARY KEY,
    icao24 VARCHAR(6) UNIQUE NOT NULL,
    registration VARCHAR(10),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    type_code VARCHAR(4),
    serial_number VARCHAR(50),
    first_flight_date DATE,
    age_years DECIMAL(4,1),
    created_at DATE DEFAULT (CURRENT_DATE),
    INDEX idx_icao24 (icao24)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Flights Table
CREATE TABLE IF NOT EXISTS flights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL,
    callsign VARCHAR(10),
    
    -- Airline Info
    airline_code VARCHAR(3),
    airline_name VARCHAR(100),
    
    -- Route Info
    origin_icao VARCHAR(4),
    origin_name VARCHAR(100),
    destination_icao VARCHAR(4),
    destination_name VARCHAR(100),
    
    -- Times
    scheduled_departure DATETIME,
    actual_departure DATETIME,
    scheduled_arrival DATETIME,
    actual_arrival DATETIME,
    
    -- Status
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    
    -- Aircraft Relationship
    aircraft_id INT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (aircraft_id) REFERENCES aircraft(id),
    INDEX idx_flight_number (flight_number),
    INDEX idx_callsign (callsign)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Flight Events Table
CREATE TABLE IF NOT EXISTS flight_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_id INT NOT NULL,
    
    -- Event Details
    event_type VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    actor VARCHAR(100),
    
    -- Payload (JSON)
    payload JSON,
    
    -- Verification
    data_hash VARCHAR(66),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
    INDEX idx_flight_id (flight_id),
    INDEX idx_data_hash (data_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Blockchain Records Table
CREATE TABLE IF NOT EXISTS blockchain_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    
    -- Transaction Details
    tx_hash VARCHAR(66) NOT NULL,
    block_number INT,
    contract_address VARCHAR(42),
    event_index INT,
    
    -- Verification
    data_hash VARCHAR(66),
    status VARCHAR(20) DEFAULT 'pending',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at DATETIME,
    
    FOREIGN KEY (event_id) REFERENCES flight_events(id) ON DELETE CASCADE,
    INDEX idx_tx_hash (tx_hash),
    INDEX idx_data_hash_record (data_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Historical Stats Table
CREATE TABLE IF NOT EXISTS historical_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Route Identification
    route_key VARCHAR(9) NOT NULL, -- ORIG-DEST
    airline_code VARCHAR(3),
    
    -- Performance Metrics
    avg_delay_minutes DECIMAL(6,2),
    on_time_percentage DECIMAL(5,2),
    total_flights INT DEFAULT 0,
    
    -- Breakdown
    avg_departure_delay DECIMAL(6,2),
    avg_arrival_delay DECIMAL(6,2),
    
    -- Sample Period
    sample_period_start DATE,
    sample_period_end DATE,
    
    created_at DATE DEFAULT (CURRENT_DATE),
    
    INDEX idx_route_key (route_key),
    INDEX idx_airline_code (airline_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- Initial Data Seeding (Optional)
-- INSERT INTO aircraft (icao24, registration, manufacturer, model, first_flight_date) VALUES ('a0b1c2', 'N12345', 'Boeing', '737-800', '2015-05-20');
