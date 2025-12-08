export interface Flight {
    id: number;
    flight_number: string;
    callsign?: string;
    airline?: {
        code: string;
        name: string;
    };
    origin?: {
        icao: string;
        name: string;
    };
    destination?: {
        icao: string;
        name: string;
    };
    scheduled?: {
        departure?: string;
        arrival?: string;
    };
    actual?: {
        departure?: string;
        arrival?: string;
    };
    status: string;
    aircraft?: Aircraft;
    departure_delay_minutes?: number;
    arrival_delay_minutes?: number;
    
    // Data source indicators
    is_mock_data?: boolean;
    data_source?: string;

    // Assembled data
    events?: FlightEvent[];
    delayAnalysis?: DelayAnalysis;
    blockchainEvents?: BlockchainEvent[];
    historicalBaseline?: HistoricalBaseline;
}

export interface Aircraft {
    id: number;
    icao24: string;
    registration?: string;
    manufacturer?: string;
    model?: string;
    type_code?: string;
    age_years?: number;
}

export interface FlightEvent {
    id: number;
    event_type: string;
    timestamp: string;
    actor: string;
    data_hash: string;
    blockchain: {
        is_verified: boolean;
        tx_hash?: string;
        block_number?: number;
    };
}

export interface DelayAnalysis {
    is_delayed: boolean;
    total_delay_minutes: number;
    category: string;
    departure_delay_minutes?: number | null;
    arrival_delay_minutes?: number | null;
    reasons: Array<{
        type: string;
        minutes: number;
        explanation: string;
        confidence: number;
    }>;
    human_readable: string;
}

export interface BlockchainEvent {
    event_type: string;
    timestamp: string;
    data_hash: string;
    tx_hash: string;
    block_number: number;
    contract_address: string;
    status: string;
}

export interface HistoricalBaseline {
    route_key: string;
    airline_code?: string | null;
    avg_delay_minutes?: number | null;
    on_time_percentage?: number | null;
    total_flights?: number | null;
    avg_departure_delay?: number | null;
    avg_arrival_delay?: number | null;
    sample_period_start?: string | null;
    sample_period_end?: string | null;
    delay_category?: string | null;
    on_time_category?: string | null;
}
