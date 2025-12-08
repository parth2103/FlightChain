# OpenSky API Debugging Guide

## Why OpenSky API Might Not Return Data

There are several reasons why the OpenSky API might not return flight data:

### 1. **Time Range Too Large**
- The `/flights/all` endpoint **requires time intervals ≤ 2 hours**
- If you query more than 2 hours, it returns an error
- **Solution**: Code now automatically chunks queries into 2-hour intervals

### 2. **No Flights in Time Range**
- The flight might not have existed during that time period
- Historical data is only available for recent flights (last 30 days)
- **Solution**: Code searches last 24 hours, but flights might be older/newer

### 3. **Callsign Format Mismatch**
- Callsigns might have different formats (e.g., "UAL120" vs "UAL 120" vs "UA120")
- OpenSky might store callsigns with spaces or different formatting
- **Solution**: Code does case-insensitive matching and trims whitespace

### 4. **API Rate Limiting**
- Anonymous users: 100 requests/day
- Registered users: 4000 requests/day
- **Solution**: Use Bearer token authentication (set `OPENSKY_ACCESS_TOKEN` in `.env`)

### 5. **Flight Not in Database**
- Some flights might not be tracked by OpenSky Network
- Not all airports have OpenSky receivers
- **Solution**: Falls back to mock data for demonstration

## Enhanced Debugging

The code now includes better logging:

```
Querying flights from [start] to [end] (chunked in 2-hour intervals)
  → Chunk [time1] to [time2]: X flights
  → Chunk [time2] to [time3]: Y flights
✓ Found Z flight(s) matching callsign 'FLIGHT123'
```

## What to Check

1. **Check backend logs** when searching for a flight:
   ```bash
   # Look for these messages in your backend terminal
   - "Querying flights from..."
   - "Chunk ...: X flights"
   - "✓ Found X flight(s) matching callsign"
   ```

2. **Check API authentication**:
   - Make sure `OPENSKY_ACCESS_TOKEN` is set in `backend/.env`
   - Or `OPENSKY_USERNAME` and `OPENSKY_PASSWORD`

3. **Check time range**:
   - The code searches last 24 hours by default
   - If flight is older/newer, it won't be found
   - Consider searching for currently active flights

4. **Try different flight numbers**:
   - Some flights might not be in OpenSky database
   - Try popular routes (e.g., major airlines between major airports)
   - Check OpenSky website first to verify flight exists

## Example Debug Output

```
Attempting to find flight in last 24 hours for UAL120...
Querying flights from 2024-12-07 10:00:00 to 2024-12-08 10:00:00 (chunked in 2-hour intervals)
  → Chunk 2024-12-07 10:00:00 to 2024-12-07 12:00:00: 150 flights
  → Chunk 2024-12-07 12:00:00 to 2024-12-07 14:00:00: 200 flights
  → Chunk 2024-12-07 14:00:00 to 2024-12-07 16:00:00: 180 flights
  ...
✓ Found 1 flight(s) matching callsign 'UAL120' out of 2500 total
Latest flight data: ICAO24=abc123, Departure=KJFK, Arrival=KSFO
✓ Found route from historical flights: KJFK -> KSFO
```

## Common Issues and Solutions

### Issue: "No flights returned"
**Solution**: 
- Flight might not exist in that time range
- Try a different flight number
- Check if flight is currently active on OpenSky website

### Issue: "Status 429" (Rate Limit)
**Solution**:
- Set `OPENSKY_ACCESS_TOKEN` in `.env` for higher rate limits
- Wait a few minutes between requests
- Use authentication

### Issue: "Status 400" (Bad Request)
**Solution**:
- Time range might be > 2 hours (should be handled automatically)
- Check timestamps are valid Unix timestamps
- Ensure begin < end

### Issue: Flights found but no route data
**Solution**:
- `estDepartureAirport` or `estArrivalAirport` might be null
- OpenSky might not have identified the airports
- This is normal for some flights

