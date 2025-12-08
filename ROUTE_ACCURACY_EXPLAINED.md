# Why Route Information May Differ

## The Issue

FlightChain might show a different route than Flightradar24 or other flight tracking services. For example:
- **FlightChain**: VHHH → KCVG (from OpenSky `/routes` endpoint)
- **Flightradar24**: ANC → MIA (actual current flight)

## Why This Happens

### OpenSky API Has Multiple Route Sources

1. **`/routes` Endpoint** (Scheduled Routes)
   - Returns **scheduled/routine routes** from OpenSky's database
   - May show common routes for a flight number
   - **NOT** the actual current flight route
   - Example: CKS181 might have a scheduled route VHHH → KCVG

2. **`/flights/all` Endpoint** (Actual Flight Tracking)
   - Returns **actual flights** based on ADS-B tracking
   - Provides `estDepartureAirport` and `estArrivalAirport`
   - These are **estimated** from actual flight tracking data
   - **More accurate** for the current flight
   - Example: Shows ANC → MIA for the actual current flight

3. **State Vectors** (Current Position)
   - Shows where the aircraft is RIGHT NOW
   - Doesn't provide origin/destination directly

## Solution Implemented

The code now **prioritizes** data sources in this order:

1. **Historical Flight Data** (`/flights/all`) - **MOST ACCURATE**
   - Gets actual tracked flights from last 24 hours
   - Uses `estDepartureAirport` and `estArrivalAirport`
   - Based on real ADS-B tracking

2. **Scheduled Routes** (`/routes`) - **LESS ACCURATE**
   - Only used if historical data not available
   - May show different route than actual flight

3. **Track Data** - For inference
   - Can be used to determine route from waypoints
   - Requires airport database for reverse geocoding

## Why Different Routes?

### Multiple Flights with Same Number

A flight number like "CKS181" can be used for different routes:
- Scheduled route: VHHH → KCVG (Hong Kong → Cincinnati)
- Actual flight: ANC → MIA (Anchorage → Miami)

This happens because:
- Airlines reuse flight numbers for different routes
- Cargo flights (like Kalitta Air) may have flexible routing
- The same flight number can operate different routes on different days

### OpenSky Database Limitations

- `/routes` endpoint may show the **most common** route for that flight number
- Not necessarily the **current** route
- Historical data is more accurate for actual flights

## What We've Fixed

✅ **Prioritize Historical Flight Data**: Now checks `/flights/all` first
✅ **Better Logging**: Shows which data source was used
✅ **More Accurate Routes**: Uses actual tracked flights instead of scheduled routes

## Expected Behavior Now

1. Search for CKS181
2. Code checks historical flights (last 24 hours)
3. Finds actual flight with ANC → MIA
4. Uses that route instead of scheduled VHHH → KCVG

If you still see different routes, it might be because:
- The actual flight hasn't been tracked yet in the last 24 hours
- The flight is using a different callsign
- OpenSky doesn't have tracking data for that specific flight

## Verification

Check the backend logs. You should see:
```
✓ Found ACTUAL route from flight tracking: ANC -> MIA
```

Instead of:
```
✓ OpenSky route found for CKS181: VHHH -> KCVG
```

The "ACTUAL route" message indicates we're using the more accurate historical flight data.

