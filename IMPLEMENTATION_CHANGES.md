# FlightChain Implementation Changes

## Summary

This document outlines the changes made to implement the **correct flow** for FlightChain where:
1. Data is fetched from OpenSky Network
2. Events are created in the database
3. **MetaMask prompts the user** to approve transactions
4. Users pay minimal gas fees via MetaMask
5. Data is displayed from blockchain

## Key Changes Made

### 1. Smart Contract Updates ✅

**File:** `blockchain/contracts/FlightEventRegistry.sol`

- **Removed `onlyAuthorized` modifier** from `recordEvent()` function
- Made `recordEvent()` **public** so any user can call it via MetaMask
- Users now pay for their own gas when recording events

### 2. Frontend - MetaMask Integration ✅

**New File:** `frontend/src/services/web3.ts`

- Added comprehensive Web3 service for MetaMask integration
- Functions include:
  - `isMetaMaskInstalled()` - Check if MetaMask is available
  - `connectMetaMask()` - Request account access
  - `recordEventViaMetaMask()` - Record event via MetaMask (direct)
  - `sendPreparedTransaction()` - Send prepared transaction via MetaMask
  - `getFlightEventsFromChain()` - Read events directly from blockchain
  - `prepareRecordEventTransaction()` - Prepare transaction without sending

**Updated:** `frontend/package.json`
- Added `ethers` v6.9.0 dependency

**Updated:** `frontend/src/app/page.tsx`
- **New Flow:**
  1. Check if MetaMask is installed
  2. Connect to MetaMask
  3. Check blockchain for existing events
  4. If not found, fetch from OpenSky
  5. Create events in database
  6. Prepare transactions for MetaMask
  7. Show modal prompting user to approve transactions
  8. User approves each transaction (pays gas)
  9. Confirm transactions in backend
  10. Read final data from blockchain
  11. Display flight details

**Updated:** `frontend/src/services/api.ts`
- Added `prepareTransaction()` - Get prepared transaction from backend
- Added `getFlightEventsFromChain()` - Read events from blockchain
- Added `getContractAddress()` - Get contract address
- Added `confirmTransaction()` - Confirm transaction after MetaMask approval

### 3. Backend - Transaction Preparation ✅

**Updated:** `backend/services/blockchain_service.py`

- **New Method:** `prepare_record_event_transaction()`
  - Prepares transaction data without executing
  - Returns transaction object that can be sent via MetaMask
  - Includes gas estimation

- **New Method:** `read_flight_events_from_chain()`
  - Reads flight events directly from blockchain
  - Bypasses database for verification

- **Removed:** Direct blockchain writes from `record_event()` when called from trace endpoint

**Updated:** `backend/routers/flights.py`
- `trace_flight_search()` now only creates events in DB
- Does NOT write to blockchain directly
- Frontend handles blockchain writes via MetaMask

**New Endpoints:** `backend/routers/blockchain.py`

1. **GET `/api/blockchain/prepare-transaction/{event_id}`**
   - Prepares transaction for an event
   - Returns transaction data for MetaMask

2. **GET `/api/blockchain/flight-events/{flight_number}`**
   - Reads events directly from blockchain
   - Returns list of on-chain events

3. **POST `/api/blockchain/confirm-transaction`**
   - Called after MetaMask confirms transaction
   - Updates `blockchain_records` table with tx hash and block number

**Updated:** `backend/schemas/blockchain.py`
- Added `PreparedTransaction` schema
- Added `FlightEventFromChain` schema

## Data Flow

### Before (Incorrect):
```
User Search → Backend → OpenSky → Backend writes to blockchain → Frontend displays
```

### After (Correct):
```
User Search → MetaMask Connect → 
  Check Blockchain (if exists, display) →
  If not: OpenSky → Create Events in DB → 
  Prepare Transactions → MetaMask Prompts → 
  User Approves (pays gas) → Transaction Confirmed → 
  Update DB → Read from Blockchain → Display
```

## User Experience

1. **User enters flight number** (e.g., "UA123")
2. **MetaMask opens** (if not connected)
3. **User approves connection**
4. **System checks blockchain** for existing events
5. **If flight not found:**
   - Fetches from OpenSky Network
   - Creates events in database
   - Shows modal: "Approve X transactions to record on blockchain"
6. **User clicks "Approve & Send"**
7. **MetaMask opens X times** (once per event)
8. **User approves each transaction** (minimal gas on Ganache)
9. **Transactions confirmed** on blockchain
10. **Flight details displayed** with blockchain verification badges

## Gas Optimization

- Smart contract uses efficient storage
- Minimal data stored on-chain (only hashes)
- Gas estimation with 20% buffer
- On Ganache testnet, gas is free for testing

## Testing Instructions

1. **Start Ganache:**
   ```bash
   cd blockchain
   npm install
   npm run ganache
   ```

2. **Deploy Contract:**
   ```bash
   npx truffle migrate --network development
   # Copy contract address to backend/.env
   ```

3. **Start Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

4. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Test Flow:**
   - Install MetaMask browser extension
   - Connect to Ganache (Localhost 8545)
   - Import a Ganache account (for free test ETH)
   - Search for a flight (e.g., "UA123")
   - Approve MetaMask transactions
   - Verify events appear on blockchain

## Environment Variables

### Backend (.env):
```
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/flightchain
GANACHE_URL=http://127.0.0.1:8545
CONTRACT_ADDRESS=0x... # From truffle migrate
```

### Frontend (.env.local):
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_GANACHE_URL=http://127.0.0.1:8545
```

## Important Notes

1. **MetaMask Required**: Users must have MetaMask installed
2. **Ganache for Testing**: Use Ganache for local development (free gas)
3. **Contract Address**: Must be set in backend config after deployment
4. **Network Configuration**: MetaMask must be connected to Ganache (Localhost 8545)
5. **Transaction Flow**: Each event requires a separate MetaMask approval

## Next Steps

1. ✅ Smart contract allows public writes
2. ✅ MetaMask integration complete
3. ✅ Transaction preparation implemented
4. ✅ Frontend flow updated
5. ⚠️ **TODO**: Add error handling for failed transactions
6. ⚠️ **TODO**: Add transaction status tracking
7. ⚠️ **TODO**: Optimize for batch transactions (optional)

## Files Modified

### Created:
- `frontend/src/services/web3.ts`

### Modified:
- `blockchain/contracts/FlightEventRegistry.sol`
- `frontend/package.json`
- `frontend/src/app/page.tsx`
- `frontend/src/services/api.ts`
- `backend/services/blockchain_service.py`
- `backend/routers/flights.py`
- `backend/routers/blockchain.py`
- `backend/schemas/blockchain.py`

All changes maintain backward compatibility where possible, but the primary flow now uses MetaMask for user-initiated transactions.

