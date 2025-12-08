# Why FlightChain Data Differs from OpenSky Website

## The Issue

When you search for a flight (e.g., UAL120), FlightChain might show:
- **Route:** KSFO → KJFK (San Francisco → New York)
- **Aircraft:** Airbus A350-900, Registration N903A

But OpenSky Network website shows:
- **Route:** EWR → BCN (Newark → Barcelona)  
- **Aircraft:** Boeing 777-200, Registration N78003

## Why This Happens

### 1. **OpenSky API Limitations**

The OpenSky Network API has restrictions:
- **`/routes` endpoint**: Only contains **scheduled routes** that are in their database
- **`/states/all` endpoint**: Only returns flights **currently in the air** or recently tracked
- **Rate Limits**: Free tier has 100 requests/day (anonymous) or 4000/day (registered)

### 2. **Fallback to Mock Data**

When FlightChain can't find data from OpenSky API:
1. Backend tries to fetch from OpenSky API
2. If no route data is found AND no current state is found
3. Backend **automatically falls back to synthetic/mock data** for demonstration
4. Mock data uses predefined routes (KSFO→KJFK is one of them)
5. Mock aircraft data is randomly generated

### 3. **OpenSky Website Uses Different Data Sources**

The OpenSky Network **website** has access to:
- More comprehensive route databases
- Historical flight data
- Real-time tracking from multiple sources
- Possibly different API endpoints or data sources

So the website can show routes and aircraft that aren't available via the public API.

## How to Identify Mock Data

FlightChain now shows a **warning banner** when mock data is used:
```
⚠️ Demo Data: This flight is using synthetic/mock data because 
real-time data from OpenSky Network was not available.
```

## Solutions

### Option 1: Use Real-Time Active Flights
Search for flights that are **currently in the air**:
- Check OpenSky Network website first
- Use flights that show as "AIRBORNE" or active
- These are more likely to be in the `/states/all` API

### Option 2: Improve OpenSky API Integration
We can enhance the backend to:
- Try multiple API endpoints
- Cache route data
- Use flight history endpoints
- Better error handling and retry logic

### Option 3: Accept Mock Data for Demo
For demonstration purposes, mock data is fine - it shows the blockchain functionality working. The important part is that:
- Events are created
- Transactions are prepared
- MetaMask integration works
- Blockchain recording works

## Current Status

✅ **Working:**
- Blockchain transaction preparation
- MetaMask integration  
- Event creation and storage
- Database storage

⚠️ **Using Mock Data When:**
- Flight not in OpenSky API routes database
- Flight not currently active/in the air
- OpenSky API rate limit reached
- API connection issues

The mock data indicator will now show up in the UI so users know when data is synthetic.

