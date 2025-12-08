# Installing OpenSky Python API (Optional)

The OpenSky Python API library is **optional**. The code will work fine without it using the REST API fallback.

## Option 1: Install from GitHub (Recommended if you want the official library)

```bash
cd backend
source venv/bin/activate
pip install git+https://github.com/openskynetwork/opensky-api.git
```

## Option 2: Use REST API (Already Working)

The code already works with the REST API fallback. You don't need to install anything! The REST API extracts the same fields (`estDepartureAirport`, `estArrivalAirport`) from the JSON response.

## What's the Difference?

- **Official Library**: Wraps the API calls in Python classes (FlightData, StateVector, etc.)
- **REST API Fallback**: Directly parses JSON responses (same data, different format)

Both methods will:
- Extract `estDepartureAirport` and `estArrivalAirport` from flight data
- Query flights in 2-hour chunks (API requirement)
- Filter by callsign
- Return the same route information

## Current Status

✅ **The code is already working** with the REST API fallback. Installing the official library is optional and will provide the same results.

If you encounter the error:
```
ERROR: Could not find a version that satisfies the requirement opensky-api>=2.2.8
```

**Don't worry!** The REST API fallback will handle everything. The code gracefully falls back if the library isn't installed.

