"""
Flight Service

Core service for flight data management.
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from models.flight import Flight
from models.aircraft import Aircraft
from models.historical_stats import HistoricalStats
from schemas.flight import (
    FlightResponse,
    FlightCreate,
    AirlineInfo,
    AirportInfo,
    ScheduleInfo,
)
from schemas.aircraft import AircraftResponse
from schemas.historical import HistoricalBaselineResponse
from services.opensky_client import OpenSkyClient, get_airline_info


from services.mock_data_generator import MockDataGenerator

class FlightService:
    """Service for flight data operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.opensky = OpenSkyClient()
        self.mock_generator = MockDataGenerator()
    
    def get_flight_by_id(self, flight_id: int) -> Optional[Flight]:
        """Get flight by ID."""
        return self.db.query(Flight).filter(Flight.id == flight_id).first()
    
    def get_flight_by_number(self, flight_number: str) -> Optional[Flight]:
        """
        Get most recent flight by flight number.
        
        Searches by flight_number and callsign.
        """
        return (
            self.db.query(Flight)
            .filter(
                (Flight.flight_number == flight_number) |
                (Flight.callsign == flight_number)
            )
            .order_by(Flight.created_at.desc())
            .first()
        )
    
    async def fetch_and_create_flight(self, flight_number: str) -> Optional[Flight]:
        """
        Fetch flight data from OpenSky and create database record.
        
        Falls back to MockDataGenerator if OpenSky returns no data.
        """
        flight_number = flight_number.upper()
        
        # 1. Try OpenSky Real Data (with error handling)
        route = None
        matching_state = None
        is_mock = False
        
        # PRIORITY 1: Get current state to find the aircraft's ICAO24
        try:
            states = await self.opensky.get_current_states()
            print(f"OpenSky states API returned {len(states)} flights")
            for state in states:
                if state.callsign and state.callsign.upper() == flight_number:
                    matching_state = state
                    print(f"✓ Found matching state for {flight_number} in OpenSky")
                    break
            if not matching_state:
                print(f"✗ No matching state found for {flight_number} in OpenSky current states")
        except Exception as e:
            print(f"Error fetching states from OpenSky: {str(e)}")
        
        # PRIORITY 2: Get route from historical flights (MOST ACCURATE - based on actual tracking)
        # This is more accurate than /routes endpoint which shows scheduled routes
        try:
            end_time = datetime.now()
            begin_time = end_time - timedelta(days=1)
            print(f"Searching for actual flight route in last 24 hours for {flight_number}...")
            flights = await self.opensky.get_flights_by_callsign(flight_number, begin_time, end_time)
            
            if flights and len(flights) > 0:
                # Sort by firstSeen to get most recent actual flight
                flights_sorted = sorted(flights, key=lambda x: x.get("firstSeen", 0), reverse=True)
                latest_flight = flights_sorted[0]
                
                icao24 = latest_flight.get("icao24")
                first_seen = latest_flight.get("firstSeen", 0)
                est_departure = latest_flight.get("estDepartureAirport")
                est_arrival = latest_flight.get("estArrivalAirport")
                
                print(f"Latest actual flight: ICAO24={icao24}, Departure={est_departure}, Arrival={est_arrival}")
                
                if est_departure and est_arrival:
                    # This is the ACTUAL route based on flight tracking - more accurate!
                    print(f"✓ Found ACTUAL route from flight tracking: {est_departure} -> {est_arrival}")
                    from services.opensky_client import FlightRoute
                    route = FlightRoute(
                        callsign=flight_number,
                        departure_airport=est_departure,
                        arrival_airport=est_arrival,
                        operator_icao=None
                    )
                    # Update matching_state if we have ICAO24 but no current state
                    if not matching_state and icao24:
                        try:
                            states = await self.opensky.get_current_states(icao24=icao24)
                            if states and len(states) > 0:
                                matching_state = states[0]
                                print(f"✓ Found current state for aircraft {icao24}")
                        except Exception as e:
                            print(f"Could not get current state: {str(e)}")
        except Exception as e:
            print(f"Error getting historical flight route: {str(e)}")
        
        # PRIORITY 3: Fallback to /routes endpoint (scheduled routes - may not match actual route)
        if not route:
            try:
                print(f"⚠️  Historical flight data not found. Trying scheduled routes from /routes endpoint...")
                print(f"   Note: Scheduled routes may differ from actual flight route")
                route = await self.opensky.get_route(flight_number)
                if route:
                    print(f"⚠️  Using scheduled route: {route.departure_airport} -> {route.arrival_airport}")
                    print(f"   This may not match the actual current flight route")
            except Exception as e:
                print(f"Error fetching route from OpenSky: {str(e)}")
        
        # PRIORITY 4: If we have matching state but still no route, try track endpoint
        if not route and matching_state:
            try:
                print(f"Attempting to get live track for ICAO24 {matching_state.icao24}...")
                track = await self.opensky.get_track(matching_state.icao24, time=0)  # Get live track
                
                if track and track.path:
                    print(f"✓ Got live track with {len(track.path)} waypoints")
                    # Could use track waypoints to determine route, but requires airport DB
            except Exception as e:
                print(f"Error fetching track data: {str(e)}")
        
        # 2. Fallback to Mock Data if needed
        if not route and not matching_state:
            print(f"⚠️  WARNING: No live data for {flight_number} from OpenSky API.")
            print(f"   This could mean:")
            print(f"   - Flight is not currently active/in the air")
            print(f"   - OpenSky API rate limit reached")
            print(f"   - Flight route not in OpenSky database")
            print(f"   - Falling back to synthetic mock data for demonstration...")
            is_mock = True
            route = self.mock_generator.generate_mock_route(flight_number)
            matching_state = self.mock_generator.generate_mock_state(flight_number)
        
        # Extract airline info
        iata_code, airline_name = get_airline_info(flight_number)
        
        # Determine Schedule
        scheduled_dep, scheduled_arr = None, None
        if is_mock:
            scheduled_dep, scheduled_arr = self.mock_generator.generate_schedule(flight_number)
            # Ensure datetime objects are naive (no timezone) for MySQL compatibility
            if scheduled_dep and scheduled_dep.tzinfo is not None:
                scheduled_dep = scheduled_dep.replace(tzinfo=None)
            if scheduled_arr and scheduled_arr.tzinfo is not None:
                scheduled_arr = scheduled_arr.replace(tzinfo=None)
        
        # Create flight record
        origin_name = None
        dest_name = None
        if route:
            origin_name = route.departure_airport
            dest_name = route.arrival_airport
        
        flight = Flight(
            flight_number=flight_number,
            callsign=flight_number,
            airline_code=iata_code,
            airline_name=airline_name,
            origin_icao=route.departure_airport if route else None,
            origin_name=origin_name,
            destination_icao=route.arrival_airport if route else None,
            destination_name=dest_name,
            scheduled_departure=scheduled_dep,
            scheduled_arrival=scheduled_arr,
            # Mock flights are usually active for demo purposes
            status="AIRBORNE" if (matching_state and not matching_state.on_ground) else "SCHEDULED",
        )
        
        # Get aircraft info
        try:
            if matching_state:
                aircraft = await self._get_or_create_aircraft(matching_state.icao24, is_mock)
                if aircraft:
                    flight.aircraft_id = aircraft.id
        except Exception as e:
            print(f"Error getting aircraft info: {str(e)}")
            # Continue without aircraft info
        
        try:
            self.db.add(flight)
            self.db.commit()
            self.db.refresh(flight)
            return flight
        except Exception as e:
            error_str = str(e)
            print(f"Error saving flight to database: {error_str}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            
            # If it's a datetime format issue, try creating a new flight with fresh datetimes
            if "isoformat" in error_str.lower() or "datetime" in error_str.lower():
                print("Attempting to fix datetime format issue...")
                try:
                    # Create a new flight object with fresh datetime objects
                    new_flight = Flight(
                        flight_number=flight.flight_number,
                        callsign=flight.callsign,
                        airline_code=flight.airline_code,
                        airline_name=flight.airline_name,
                        origin_icao=flight.origin_icao,
                        destination_icao=flight.destination_icao,
                        scheduled_departure=scheduled_dep,  # Use original datetime objects
                        scheduled_arrival=scheduled_arr,
                        status=flight.status,
                        aircraft_id=flight.aircraft_id,
                    )
                    self.db.add(new_flight)
                    self.db.commit()
                    self.db.refresh(new_flight)
                    return new_flight
                except Exception as e2:
                    print(f"Retry with new flight object also failed: {str(e2)}")
                    self.db.rollback()
            
            raise
    
    async def _get_or_create_aircraft(self, icao24: str, is_mock: bool = False) -> Optional[Aircraft]:
        """Get or create aircraft record."""
        # Check if exists
        aircraft = self.db.query(Aircraft).filter(Aircraft.icao24 == icao24).first()
        if aircraft:
            return aircraft
        
        # Fetch metadata
        metadata = None
        if is_mock:
            metadata = self.mock_generator.generate_mock_aircraft(icao24)
        else:
            metadata = await self.opensky.get_aircraft_metadata(icao24)
            
        if not metadata:
            return None
        
        aircraft = Aircraft(
            icao24=icao24,
            registration=metadata.registration,
            manufacturer=metadata.manufacturer,
            model=metadata.model,
            type_code=metadata.type_code,
            serial_number=metadata.serial_number,
        )
        
        self.db.add(aircraft)
        self.db.commit()
        self.db.refresh(aircraft)
        
        return aircraft
    
    def get_aircraft_by_icao24(self, icao24: str) -> Optional[Aircraft]:
        """Get aircraft by ICAO24 address."""
        return self.db.query(Aircraft).filter(Aircraft.icao24 == icao24).first()
    
    def get_historical_baseline(self, flight: Flight) -> Optional[HistoricalBaselineResponse]:
        """Get historical baseline for flight's route."""
        if not flight.origin_icao or not flight.destination_icao:
            return None
        
        route_key = f"{flight.origin_icao}-{flight.destination_icao}"
        
        stats = (
            self.db.query(HistoricalStats)
            .filter(HistoricalStats.route_key == route_key)
            .filter(
                (HistoricalStats.airline_code == flight.airline_code) |
                (HistoricalStats.airline_code.is_(None))
            )
            .first()
        )
        
        if not stats:
            return None
        
        return HistoricalBaselineResponse(
            route_key=stats.route_key,
            airline_code=stats.airline_code,
            avg_delay_minutes=float(stats.avg_delay_minutes) if stats.avg_delay_minutes else None,
            on_time_percentage=float(stats.on_time_percentage) if stats.on_time_percentage else None,
            total_flights=stats.total_flights,
            avg_departure_delay=float(stats.avg_departure_delay) if stats.avg_departure_delay else None,
            avg_arrival_delay=float(stats.avg_arrival_delay) if stats.avg_arrival_delay else None,
            sample_period_start=stats.sample_period_start,
            sample_period_end=stats.sample_period_end,
            delay_category=stats.delay_category,
            on_time_category=stats.on_time_category,
        )
    
    def to_response(self, flight: Flight) -> FlightResponse:
        """Convert Flight model to response schema."""
        airline = None
        if flight.airline_code or flight.airline_name:
            airline = AirlineInfo(
                code=flight.airline_code or "",
                name=flight.airline_name or ""
            )
        
        origin = None
        if flight.origin_icao:
            origin = AirportInfo(
                icao=flight.origin_icao,
                name=flight.origin_name or flight.origin_icao
            )
        
        destination = None
        if flight.destination_icao:
            destination = AirportInfo(
                icao=flight.destination_icao,
                name=flight.destination_name or flight.destination_icao
            )
        
        scheduled = None
        if flight.scheduled_departure or flight.scheduled_arrival:
            scheduled = ScheduleInfo(
                departure=flight.scheduled_departure,
                arrival=flight.scheduled_arrival
            )
        
        actual = None
        if flight.actual_departure or flight.actual_arrival:
            actual = ScheduleInfo(
                departure=flight.actual_departure,
                arrival=flight.actual_arrival
            )
        
        aircraft = None
        if flight.aircraft:
            aircraft = AircraftResponse(
                id=flight.aircraft.id,
                icao24=flight.aircraft.icao24,
                registration=flight.aircraft.registration,
                manufacturer=flight.aircraft.manufacturer,
                model=flight.aircraft.model,
                type_code=flight.aircraft.type_code,
                serial_number=flight.aircraft.serial_number,
                first_flight_date=flight.aircraft.first_flight_date,
                age_years=float(flight.aircraft.age_years) if flight.aircraft.age_years else None,
                full_type=flight.aircraft.full_type,
            )
        
        # Check if this flight was created with mock data
        # We'll add a flag to track this (for now, we'll infer from the route pattern)
        is_mock = False
        data_source = "opensky"
        # Heuristic: if route is one of the mock routes, it's likely mock data
        if flight.origin_icao and flight.destination_icao:
            mock_routes = [("KSFO", "KJFK"), ("KJFK", "EGLL"), ("KLAX", "RJAA"), 
                          ("KORD", "KLAX"), ("EGLL", "OMDB"), ("WMKK", "WSSS"), ("VABB", "OMDB")]
            if (flight.origin_icao, flight.destination_icao) in mock_routes:
                is_mock = True
                data_source = "mock"
        
        return FlightResponse(
            id=flight.id,
            flight_number=flight.flight_number,
            callsign=flight.callsign,
            airline=airline,
            origin=origin,
            destination=destination,
            scheduled=scheduled,
            actual=actual,
            status=flight.status,
            aircraft=aircraft,
            departure_delay_minutes=flight.departure_delay_minutes,
            is_mock_data=is_mock,
            data_source=data_source,
            arrival_delay_minutes=flight.arrival_delay_minutes,
        )
