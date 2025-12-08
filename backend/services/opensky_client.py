"""
OpenSky Network Client

Service for fetching real-time flight data from the OpenSky Network API.
"""

import httpx
import time
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import quote
from config import settings


@dataclass
class FlightState:
    """Represents a flight state from OpenSky."""
    icao24: str
    callsign: Optional[str]
    origin_country: str
    time_position: Optional[int]
    last_contact: int
    longitude: Optional[float]
    latitude: Optional[float]
    baro_altitude: Optional[float]
    on_ground: bool
    velocity: Optional[float]
    true_track: Optional[float]
    vertical_rate: Optional[float]
    sensors: Optional[list[int]]
    geo_altitude: Optional[float]
    squawk: Optional[str]
    spi: bool
    position_source: int


@dataclass
class FlightRoute:
    """Represents a flight route from OpenSky."""
    callsign: str
    departure_airport: Optional[str]
    arrival_airport: Optional[str]
    operator_icao: Optional[str]


@dataclass
class Waypoint:
    """A waypoint in a flight track."""
    time: int
    latitude: Optional[float]
    longitude: Optional[float]
    baro_altitude: Optional[float]
    true_track: Optional[float]
    on_ground: bool


@dataclass
class FlightTrack:
    """Flight track/trajectory from OpenSky."""
    icao24: str
    start_time: int
    end_time: int
    callsign: Optional[str]
    path: list[Waypoint]


@dataclass
class AircraftMetadata:
    """Aircraft metadata from OpenSky."""
    icao24: str
    registration: Optional[str]
    manufacturer: Optional[str]
    model: Optional[str]
    type_code: Optional[str]
    serial_number: Optional[str]
    operator: Optional[str]
    first_flight_date: Optional[str]


class OpenSkyClient:
    """
    Client for the OpenSky Network API.
    
    API Documentation: https://openskynetwork.github.io/opensky-api/
    
    Note: Free tier has rate limits:
    - Anonymous: 100 requests/day
    - Registered: 4000 requests/day
    """
    
    def __init__(self):
        self.base_url = settings.opensky_base_url
        self.auth_url = settings.opensky_auth_url
        self.username = settings.opensky_username
        self.password = settings.opensky_password
        self.access_token = settings.opensky_access_token
        self.client_id = settings.opensky_client_id
        self.client_secret = settings.opensky_client_secret
        self.timeout = settings.opensky_timeout
        
        # Token management for OAuth
        self.token_expires_at = 0
        
        # Set up authentication - prefer OAuth, then Bearer token, then basic auth
        self.auth = None
        self.headers = {}
        
        if self.client_id and self.client_secret:
            # Use OAuth 2.0 client credentials flow (preferred)
            print("Using OAuth 2.0 authentication for OpenSky Network")
            self._authenticate_oauth()
        elif self.access_token:
            # Use pre-obtained Bearer token
            print("Using Bearer token authentication for OpenSky Network")
            self.headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.username and self.password:
            # Fallback to basic auth
            print("Using basic authentication for OpenSky Network")
            self.auth = (self.username, self.password)
    
    def _authenticate_oauth(self) -> bool:
        """
        Authenticate with OpenSky Network using OAuth 2.0 client credentials.
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.client_id or not self.client_secret:
            return False
        
        try:
            payload = (
                f"grant_type=client_credentials"
                f"&client_id={quote(self.client_id)}"
                f"&client_secret={quote(self.client_secret)}"
            )
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Use synchronous request for token exchange
            import requests
            response = requests.post(
                self.auth_url,
                headers=headers,
                data=payload,
                timeout=30
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 1800)  # Default 30 minutes
            
            # Set expiry time with 60 second buffer
            self.token_expires_at = time.time() + expires_in - 60
            
            # Set authorization header
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            print(f"✓ OpenSky OAuth authentication successful (token expires in {expires_in}s)")
            return True
            
        except Exception as e:
            print(f"⚠️  OpenSky OAuth authentication failed: {str(e)}")
            print("   Falling back to anonymous access (limited rate)")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if needed.
        
        Returns:
            True if authenticated, False otherwise
        """
        # Only check token expiry if using OAuth
        if self.client_id and self.client_secret:
            if time.time() >= self.token_expires_at:
                return self._authenticate_oauth()
        return True
    
    async def get_current_states(
        self,
        icao24: Optional[str] = None,
        bounds: Optional[tuple[float, float, float, float]] = None
    ) -> list[FlightState]:
        """
        Get current flight states.
        
        Args:
            icao24: Filter by ICAO24 address
            bounds: Bounding box (min_lat, max_lat, min_lon, max_lon)
            
        Returns:
            List of FlightState objects
        """
        url = f"{self.base_url}/states/all"
        params = {}
        
        if icao24:
            params["icao24"] = icao24.lower()
        
        if bounds:
            params["lamin"] = bounds[0]
            params["lamax"] = bounds[1]
            params["lomin"] = bounds[2]
            params["lomax"] = bounds[3]
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, auth=self.auth, headers=self.headers)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            states = data.get("states", []) or []
            
            return [self._parse_state(s) for s in states]
    
    async def get_flights_by_callsign(
        self,
        callsign: str,
        begin: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> list[dict]:
        """
        Get flights by callsign within a time range.
        
        Uses the official OpenSky Python API to get FlightData objects
        which contain estDepartureAirport and estArrivalAirport.
        
        Args:
            callsign: Flight callsign
            begin: Start time (default: 24 hours ago)
            end: End time (default: now)
            
        Returns:
            List of flight data dictionaries with estDepartureAirport and estArrivalAirport
        """
        try:
            # Try using official OpenSky Python API
            import opensky_api
            
            # Create API instance
            api = opensky_api.OpenSkyApi(
                username=self.username,
                password=self.password
            )
            
            if end is None:
                end = datetime.now()
            if begin is None:
                begin = end - timedelta(days=1)
            
            # Use official API to get flights in interval
            # Time interval must be <= 2 hours, so we need to query in chunks
            flights_data = []
            current_begin = begin
            
            while current_begin < end:
                current_end = min(current_begin + timedelta(hours=2), end)
                
                try:
                    # Run sync API call in executor to avoid blocking
                    import asyncio
                    loop = asyncio.get_event_loop()
                    flights_chunk = await loop.run_in_executor(
                        None,
                        lambda: api.get_flights_from_interval(
                            int(current_begin.timestamp()),
                            int(current_end.timestamp())
                        )
                    )
                    
                    if flights_chunk:
                        # Filter by callsign and convert FlightData to dict
                        for flight in flights_chunk:
                            if flight.callsign and flight.callsign.strip().upper() == callsign.upper():
                                flights_data.append({
                                    "icao24": flight.icao24,
                                    "firstSeen": flight.firstSeen,
                                    "lastSeen": flight.lastSeen,
                                    "estDepartureAirport": flight.estDepartureAirport,
                                    "estArrivalAirport": flight.estArrivalAirport,
                                    "callsign": flight.callsign,
                                    "estDepartureAirportHorizDistance": getattr(flight, 'estDepartureAirportHorizDistance', None),
                                    "estArrivalAirportHorizDistance": getattr(flight, 'estArrivalAirportHorizDistance', None),
                                })
                except Exception as e:
                    print(f"Error fetching flights chunk {current_begin} to {current_end}: {str(e)}")
                
                current_begin = current_end
            
            if flights_data:
                print(f"✓ Found {len(flights_data)} flight(s) using official OpenSky API")
                return flights_data
                
        except ImportError:
            print("⚠️  opensky-api library not installed, falling back to REST API")
        except Exception as e:
            print(f"Error using official OpenSky API: {str(e)}, falling back to REST API")
        
        # Fallback to REST API
        # The REST API returns the same data structure, so we can extract estDepartureAirport/estArrivalAirport
        if end is None:
            end = datetime.now()
        if begin is None:
            begin = end - timedelta(days=1)
        
        # Time interval must be <= 2 hours for /flights/all endpoint
        # So we query in chunks
        flights_data = []
        current_begin = begin
        
        while current_begin < end:
            current_end = min(current_begin + timedelta(hours=2), end)
            
            url = f"{self.base_url}/flights/all"
            params = {
                "begin": int(current_begin.timestamp()),
                "end": int(current_end.timestamp())
            }
            
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params, auth=self.auth, headers=self.headers)
                    
                    if response.status_code == 200:
                        flights = response.json()
                        
                        # Filter by callsign and extract route data
                        matched_count = 0
                        for flight in flights:
                            flight_callsign = flight.get("callsign", "").strip() if flight.get("callsign") else ""
                            if flight_callsign.upper() == callsign.upper():
                                matched_count += 1
                                est_dep = flight.get("estDepartureAirport")
                                est_arr = flight.get("estArrivalAirport")
                                print(f"  ✓ Matched: {flight_callsign} ({est_dep} -> {est_arr})")
                                flights_data.append({
                                    "icao24": flight.get("icao24"),
                                    "firstSeen": flight.get("firstSeen", 0),
                                    "lastSeen": flight.get("lastSeen", 0),
                                    "estDepartureAirport": flight.get("estDepartureAirport"),
                                    "estArrivalAirport": flight.get("estArrivalAirport"),
                                    "callsign": flight.get("callsign"),
                                    "estDepartureAirportHorizDistance": flight.get("estDepartureAirportHorizDistance"),
                                    "estArrivalAirportVertDistance": flight.get("estDepartureAirportVertDistance"),
                                    "estArrivalAirportHorizDistance": flight.get("estArrivalAirportHorizDistance"),
                                    "estArrivalAirportVertDistance": flight.get("estArrivalAirportVertDistance"),
                                })
            except Exception as e:
                print(f"Error fetching flights chunk {current_begin} to {current_end}: {str(e)}")
            
            current_begin = current_end
        
        if flights_data:
            print(f"✓ Found {len(flights_data)} flight(s) using REST API")
            return flights_data
        
        return []
    
    async def get_aircraft_metadata(self, icao24: str) -> Optional[AircraftMetadata]:
        """
        Get aircraft metadata by ICAO24 address.
        
        Args:
            icao24: ICAO24 address
            
        Returns:
            AircraftMetadata or None
        """
        url = f"{self.base_url}/metadata/aircraft/icao/{icao24.lower()}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, auth=self.auth, headers=self.headers)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            return AircraftMetadata(
                icao24=icao24.lower(),
                registration=data.get("registration"),
                manufacturer=data.get("manufacturerName"),
                model=data.get("model"),
                type_code=data.get("typecode"),
                serial_number=data.get("serialNumber"),
                operator=data.get("operator"),
                first_flight_date=data.get("firstFlightDate")
            )
    
    async def get_route(self, callsign: str) -> Optional[FlightRoute]:
        """
        Get route information for a callsign.
        
        Args:
            callsign: Flight callsign
            
        Returns:
            FlightRoute or None
        """
        url = f"{self.base_url}/routes"
        params = {"callsign": callsign.upper()}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, auth=self.auth, headers=self.headers)
                
                if response.status_code != 200:
                    print(f"OpenSky routes API returned status {response.status_code} for {callsign}")
                    return None
                
                data = response.json()
                
                # Check if route data exists and is valid
                route_list = data.get("route", [])
                if not route_list or len(route_list) < 2:
                    print(f"OpenSky routes API returned invalid route data for {callsign}: {data}")
                    return None
                
                departure = route_list[0]
                arrival = route_list[-1]
                
                if not departure or not arrival:
                    print(f"OpenSky routes API returned empty departure/arrival for {callsign}")
                    return None
                
                print(f"✓ OpenSky route found for {callsign}: {departure} -> {arrival}")
                return FlightRoute(
                    callsign=callsign.upper(),
                    departure_airport=departure,
                    arrival_airport=arrival,
                    operator_icao=data.get("operatorIata")
                )
        except Exception as e:
            print(f"Error fetching route from OpenSky for {callsign}: {str(e)}")
            return None
    
    async def get_track(self, icao24: str, time: Optional[int] = None) -> Optional[FlightTrack]:
        """
        Get flight track/trajectory for an aircraft.
        
        Args:
            icao24: ICAO24 address (lowercase hex)
            time: Unix timestamp. If 0 or None, gets live track if available.
            
        Returns:
            FlightTrack or None
        """
        url = f"{self.base_url}/tracks"
        params = {
            "icao24": icao24.lower(),
            "time": time or 0
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, auth=self.auth, headers=self.headers)
                
                if response.status_code != 200:
                    print(f"OpenSky tracks API returned status {response.status_code} for {icao24}")
                    return None
                
                data = response.json()
                
                if not data or "path" not in data:
                    return None
                
                # Parse waypoints
                waypoints = []
                for point in data.get("path", []):
                    if len(point) >= 6:
                        waypoints.append(Waypoint(
                            time=point[0],
                            latitude=point[1],
                            longitude=point[2],
                            baro_altitude=point[3],
                            true_track=point[4],
                            on_ground=point[5] if len(point) > 5 else False
                        ))
                
                print(f"✓ OpenSky track found for {icao24}: {len(waypoints)} waypoints")
                return FlightTrack(
                    icao24=data.get("icao24", icao24.lower()),
                    start_time=data.get("startTime", 0),
                    end_time=data.get("endTime", 0),
                    callsign=data.get("callsign"),
                    path=waypoints
                )
        except Exception as e:
            print(f"Error fetching track from OpenSky for {icao24}: {str(e)}")
            return None
    
    async def get_flights_in_time_range(
        self,
        begin: datetime,
        end: datetime,
        callsign: Optional[str] = None
    ) -> list[dict]:
        """
        Get flights within a time range.
        
        Args:
            begin: Start time
            end: End time
            callsign: Optional filter by callsign
            
        Returns:
            List of flight dictionaries with icao24, firstSeen, lastSeen, etc.
        """
        url = f"{self.base_url}/flights/all"
        params = {
            "begin": int(begin.timestamp()),
            "end": int(end.timestamp())
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, auth=self.auth, headers=self.headers)
                
                if response.status_code != 200:
                    print(f"OpenSky flights/all API returned status {response.status_code}")
                    return []
                
                flights = response.json()
                
                # Filter by callsign if provided
                if callsign:
                    flights = [
                        f for f in flights
                        if f.get("callsign", "").strip().upper() == callsign.upper()
                    ]
                
                print(f"✓ Found {len(flights)} flight(s) in time range")
                return flights
        except Exception as e:
            print(f"Error fetching flights in time range: {str(e)}")
            return None
    
    def _parse_state(self, state: list) -> FlightState:
        """Parse raw state array into FlightState object."""
        return FlightState(
            icao24=state[0],
            callsign=state[1].strip() if state[1] else None,
            origin_country=state[2],
            time_position=state[3],
            last_contact=state[4],
            longitude=state[5],
            latitude=state[6],
            baro_altitude=state[7],
            on_ground=state[8],
            velocity=state[9],
            true_track=state[10],
            vertical_rate=state[11],
            sensors=state[12],
            geo_altitude=state[13],
            squawk=state[14],
            spi=state[15],
            position_source=state[16]
        )


# Airline code mappings (subset for demonstration)
AIRLINE_CODES = {
    "UAL": ("UA", "United Airlines"),
    "AAL": ("AA", "American Airlines"),
    "DAL": ("DL", "Delta Air Lines"),
    "SWA": ("WN", "Southwest Airlines"),
    "JBU": ("B6", "JetBlue Airways"),
    "ASA": ("AS", "Alaska Airlines"),
    "FFT": ("F9", "Frontier Airlines"),
    "NKS": ("NK", "Spirit Airlines"),
    "HAL": ("HA", "Hawaiian Airlines"),
    "SKW": ("OO", "SkyWest Airlines"),
}


def get_airline_info(callsign: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract airline IATA code and name from callsign.
    
    Args:
        callsign: Flight callsign (e.g., UAL123)
        
    Returns:
        Tuple of (IATA code, airline name)
    """
    if not callsign or len(callsign) < 3:
        return None, None
    
    # Try first 3 characters as ICAO code
    icao_prefix = callsign[:3].upper()
    if icao_prefix in AIRLINE_CODES:
        return AIRLINE_CODES[icao_prefix]
    
    return None, None
