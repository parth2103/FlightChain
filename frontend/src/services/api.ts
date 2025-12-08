import axios from 'axios';

// API Client configuration
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const fetchFlightData = async (flightIdOrNumber: string, retries = 3) => {
    for (let attempt = 0; attempt < retries; attempt++) {
        try {
            console.log(`Fetching flight data for: ${flightIdOrNumber} (attempt ${attempt + 1}/${retries})`);
            
            // Try to search by flight number first (handles both IDs and flight numbers)
            const searchRes = await api.get(`/search-flight/${flightIdOrNumber}`);

            if (searchRes.data.found && searchRes.data.flight) {
                const flight = searchRes.data.flight;
                console.log(`Flight found: ID=${flight.id}, Number=${flight.flight_number}`);

                // Fetch related data in parallel with timeout protection
                try {
                    const fetchPromises = [
                        api.get(`/flight/${flight.id}/events`).catch(e => ({ status: 'rejected', reason: e })),
                        api.get(`/flight/${flight.id}/delay-analysis`).catch(e => ({ status: 'rejected', reason: e })),
                        api.get(`/flight/${flight.id}/blockchain-events`).catch(e => ({ status: 'rejected', reason: e })),
                        api.get(`/flight/${flight.id}/historical-baseline`).catch(e => ({ status: 'rejected', reason: e }))
                    ];
                    
                    // Add timeout to prevent hanging
                    const timeoutPromise = new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Data fetch timeout')), 10000)
                    );
                    
                    const [eventsRes, delayRes, blockchainRes, baselineRes] = await Promise.race([
                        Promise.allSettled(fetchPromises),
                        timeoutPromise
                    ]) as any;

                    // Handle results
                    const events = eventsRes?.status === 'fulfilled' ? eventsRes.value.data : (eventsRes?.value?.data || []);
                    const delayAnalysis = delayRes?.status === 'fulfilled' ? delayRes.value.data : (delayRes?.value?.data || null);
                    const blockchainEvents = blockchainRes?.status === 'fulfilled' ? blockchainRes.value.data : (blockchainRes?.value?.data || []);
                    const historicalBaseline = baselineRes?.status === 'fulfilled' ? baselineRes.value.data : (baselineRes?.value?.data || null);

                    return {
                        ...flight,
                        events: Array.isArray(events) ? events : [],
                        delayAnalysis: delayAnalysis,
                        blockchainEvents: Array.isArray(blockchainEvents) ? blockchainEvents : [],
                        historicalBaseline: historicalBaseline,
                    };
                } catch (error: any) {
                    // If flight exists but related data fails, still return the flight with empty arrays
                    console.warn('Some flight data failed to load (using fallbacks):', error.message);
                    return {
                        ...flight,
                        events: [],
                        delayAnalysis: null,
                        blockchainEvents: [],
                        historicalBaseline: null,
                    };
                }
            }

            // If not found and we have retries left, wait and try again
            if (attempt < retries - 1) {
                console.log(`Flight not found, retrying... (${attempt + 1}/${retries})`);
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s between retries
                continue;
            }

            throw new Error(searchRes.data.message || `Flight "${flightIdOrNumber}" not found`);
        } catch (error: any) {
            console.error(`Flight fetch attempt ${attempt + 1} failed:`, error.message);
            if (attempt === retries - 1) {
                // Last attempt failed
                throw error;
            }
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
};

export const verifyHash = async (hash: string) => {
    const res = await api.get(`/blockchain/verify/${hash}`);
    return res.data;
};

export const traceFlight = async (flightNumber: string) => {
    const res = await api.get(`/search-flight/trace/${flightNumber}`);
    return res.data;
};

export const prepareTransaction = async (eventId: number) => {
    const res = await api.get(`/blockchain/prepare-transaction/${eventId}`);
    return res.data;
};

export const getFlightEventsFromChain = async (flightNumber: string) => {
    const res = await api.get(`/blockchain/flight-events/${flightNumber}`);
    return res.data;
};

export const getContractAddress = async () => {
    const res = await api.get('/blockchain/stats');
    return res.data.contract_address;
};

export const confirmTransaction = async (eventId: number, txHash: string, blockNumber?: number) => {
    const res = await api.post('/blockchain/confirm-transaction', {
        event_id: eventId,
        tx_hash: txHash,
        block_number: blockNumber
    });
    return res.data;
};

export default api;
