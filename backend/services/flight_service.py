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
from services.csv_flight_service import CSVFlightService
from services.mock_data_generator import MockDataGenerator

# Helper function to extract airline info from flight number
def get_airline_info(flight_number: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract airline IATA code and name from flight number.
    
    Args:
        flight_number: Full flight number (e.g., "UA1545")
    
    Returns:
        Tuple of (iata_code, airline_name)
    """
    flight_number = flight_number.upper().strip()
    
    # Try to extract carrier code (usually 2-3 letters)
    carrier = None
    for length in [2, 3]:
        if len(flight_number) > length:
            potential_carrier = flight_number[:length]
            # Check if it looks like a carrier code (all letters)
            if potential_carrier.isalpha():
                carrier = potential_carrier
                break
    
    if carrier:
        # Get airline name from CSV service
        csv_service = CSVFlightService()
        airline_name = csv_service.get_airline_name(carrier)
        return carrier, airline_name or f"{carrier} Airlines"
    
    return None, None

class FlightService:
    """Service for flight data operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.csv_service = CSVFlightService()
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
        Fetch flight data from CSV database and create database record.
        
        Falls back to MockDataGenerator if CSV returns no data.
        """
        flight_number = flight_number.upper()
        is_mock = False
        
        # Try to find flight in CSV
        csv_flight = self.csv_service.find_flight_by_full_number(flight_number)
        
        if csv_flight:
            print(f"✓ Found flight {flight_number} in CSV database")
            
            # Extract airline info
            iata_code = csv_flight.carrier
            airline_name = csv_flight.airline_name or f"{csv_flight.carrier} Airlines"
            
            # Convert CSV times to datetime (using current date, preserving time)
            # Note: CSV has historical dates (2013), but we show flights as if they're today
            scheduled_dep = self.csv_service.csv_time_to_datetime(
                csv_flight.year, csv_flight.month, csv_flight.day, csv_flight.sched_dep_time, use_current_date=True
            )
            scheduled_arr = self.csv_service.csv_time_to_datetime(
                csv_flight.year, csv_flight.month, csv_flight.day, csv_flight.sched_arr_time, use_current_date=True
            )
            actual_dep = self.csv_service.csv_time_to_datetime(
                csv_flight.year, csv_flight.month, csv_flight.day, csv_flight.dep_time, use_current_date=True
            )
            actual_arr = self.csv_service.csv_time_to_datetime(
                csv_flight.year, csv_flight.month, csv_flight.day, csv_flight.arr_time, use_current_date=True
            )
            
            # Debug logging for time conversion
            print(f"Flight {flight_number} time conversion:")
            print(f"  CSV times: sched_dep={csv_flight.sched_dep_time}, sched_arr={csv_flight.sched_arr_time}, dep={csv_flight.dep_time}, arr={csv_flight.arr_time}")
            print(f"  Converted: sched_dep={scheduled_dep}, sched_arr={scheduled_arr}, dep={actual_dep}, arr={actual_arr}")
            
            # Handle arrival time - if arrival is earlier than departure, it's next day (crosses midnight)
            if scheduled_arr and scheduled_dep and scheduled_arr < scheduled_dep:
                # Arrival is next day (crosses midnight)
                scheduled_arr = scheduled_arr + timedelta(days=1)
            if actual_arr and actual_dep and actual_arr < actual_dep:
                # Actual arrival is next day
                actual_arr = actual_arr + timedelta(days=1)
            
            # Determine status based on current time and flight times
            now = datetime.now()
            status = "SCHEDULED"
            
            if scheduled_dep:
                if actual_arr:
                    # Flight has actual arrival time - check if it's in the past
                    if actual_arr <= now:
                        status = "ARRIVED"
                    elif actual_dep and actual_dep <= now:
                        status = "DEPARTED"
                    elif scheduled_dep <= now:
                        status = "DEPARTED"  # Past scheduled time but no actual departure yet
                elif actual_dep:
                    # Has actual departure but no arrival
                    if actual_dep <= now:
                        status = "AIRBORNE"
                elif scheduled_dep <= now:
                    # Past scheduled departure time
                    status = "DEPARTED"
                else:
                    # Future scheduled time
                    status = "SCHEDULED"
            
            # Create flight record
            flight = Flight(
                flight_number=flight_number,
                callsign=flight_number,
                airline_code=iata_code,
                airline_name=airline_name,
                origin_icao=csv_flight.origin,
                origin_name=csv_flight.origin,
                destination_icao=csv_flight.dest,
                destination_name=csv_flight.dest,
                scheduled_departure=scheduled_dep,
                scheduled_arrival=scheduled_arr,
                actual_departure=actual_dep,
                actual_arrival=actual_arr,
                status=status,
            )
            
            # Try to get/create aircraft from tailnum if available
            if csv_flight.tailnum:
                try:
                    aircraft = await self._get_or_create_aircraft_from_tailnum(csv_flight.tailnum)
                    if aircraft:
                        flight.aircraft_id = aircraft.id
                except Exception as e:
                    print(f"Error getting aircraft info from tailnum: {str(e)}")
            
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
                raise
        
        else:
            # Flight not found in CSV, fallback to mock data
            print(f"⚠️  WARNING: Flight {flight_number} not found in CSV database.")
            print(f"   Falling back to synthetic mock data for demonstration...")
            is_mock = True
            
            # Extract airline info
            iata_code, airline_name = get_airline_info(flight_number)
            
            # Generate mock route and schedule
            route = self.mock_generator.generate_mock_route(flight_number)
            scheduled_dep, scheduled_arr = self.mock_generator.generate_schedule(flight_number)
            
            # Ensure datetime objects are naive (no timezone) for MySQL compatibility
            if scheduled_dep and scheduled_dep.tzinfo is not None:
                scheduled_dep = scheduled_dep.replace(tzinfo=None)
            if scheduled_arr and scheduled_arr.tzinfo is not None:
                scheduled_arr = scheduled_arr.replace(tzinfo=None)
            
            # Generate mock aircraft state for ICAO24
            from services.mock_data_generator import MockDataGenerator
            matching_state = self.mock_generator.generate_mock_state(flight_number)
            
            # Create flight record
            flight = Flight(
                flight_number=flight_number,
                callsign=flight_number,
                airline_code=iata_code,
                airline_name=airline_name,
                origin_icao=route.departure_airport if route else None,
                origin_name=route.departure_airport if route else None,
                destination_icao=route.arrival_airport if route else None,
                destination_name=route.arrival_airport if route else None,
                scheduled_departure=scheduled_dep,
                scheduled_arrival=scheduled_arr,
                status="AIRBORNE" if (matching_state and not matching_state.on_ground) else "SCHEDULED",
            )
            
            # Get mock aircraft info
            try:
                if matching_state:
                    aircraft = await self._get_or_create_aircraft(matching_state.icao24, is_mock=True)
                    if aircraft:
                        flight.aircraft_id = aircraft.id
            except Exception as e:
                print(f"Error getting aircraft info: {str(e)}")
            
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
                raise
    
    async def _get_or_create_aircraft_from_tailnum(self, tailnum: str) -> Optional[Aircraft]:
        """Get or create aircraft record from tail number (registration)."""
        # Check if exists by registration
        aircraft = self.db.query(Aircraft).filter(Aircraft.registration == tailnum).first()
        if aircraft:
            return aircraft
        
        # Generate mock aircraft from tailnum (we don't have metadata API anymore)
        # Use tailnum as ICAO24 equivalent for lookup
        icao24 = self._tailnum_to_icao24(tailnum)
        metadata = self.mock_generator.generate_mock_aircraft(icao24)
        
        # Override registration with actual tailnum
        if metadata:
            metadata.registration = tailnum
        
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
    
    def _tailnum_to_icao24(self, tailnum: str) -> str:
        """Convert tail number to a consistent ICAO24-like identifier."""
        # Use hash of tailnum to create consistent 6-char hex ID
        h = hash(tailnum)
        return hex(abs(h))[-6:].zfill(6)
    
    async def _get_or_create_aircraft(self, icao24: str, is_mock: bool = False) -> Optional[Aircraft]:
        """Get or create aircraft record."""
        # Check if exists
        aircraft = self.db.query(Aircraft).filter(Aircraft.icao24 == icao24).first()
        if aircraft:
            return aircraft
        
        # Generate mock aircraft (we no longer have OpenSky metadata API)
        metadata = self.mock_generator.generate_mock_aircraft(icao24)
            
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
        """
        Get historical baseline for flight's route.
        
        Calculates statistics from CSV data for the same route.
        """
        if not flight.origin_icao or not flight.destination_icao:
            return None
        
        route_key = f"{flight.origin_icao}-{flight.destination_icao}"
        
        # First check database cache
        stats = (
            self.db.query(HistoricalStats)
            .filter(HistoricalStats.route_key == route_key)
            .filter(
                (HistoricalStats.airline_code == flight.airline_code) |
                (HistoricalStats.airline_code.is_(None))
            )
            .first()
        )
        
        if stats:
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
        
        # Calculate from CSV data if not in database
        return self._calculate_baseline_from_csv(route_key, flight.airline_code)
    
    def _calculate_baseline_from_csv(self, route_key: str, airline_code: Optional[str] = None) -> Optional[HistoricalBaselineResponse]:
        """
        Calculate historical baseline from CSV data for a route.
        
        Args:
            route_key: Route key in format "ORIG-DEST"
            airline_code: Optional airline code to filter by
        
        Returns:
            HistoricalBaselineResponse or None
        """
        # Parse route key
        parts = route_key.split('-')
        if len(parts) != 2:
            return None
        
        origin = parts[0]
        dest = parts[1]
        
        # Ensure CSV is loaded
        self.csv_service._load_flights()
        
        # Get all flights for this route from CSV
        matching_flights = []
        for key, flights in self.csv_service._flights_cache.items():
            for flight_data in flights:
                if flight_data.origin == origin and flight_data.dest == dest:
                    if not airline_code or flight_data.carrier == airline_code:
                        matching_flights.append(flight_data)
        
        if not matching_flights:
            return None
        
        # Calculate statistics
        dep_delays = []
        arr_delays = []
        on_time_count = 0
        total_flights = len(matching_flights)
        ON_TIME_THRESHOLD = 15  # 15 minutes
        
        for flight_data in matching_flights:
            if flight_data.dep_delay is not None:
                dep_delays.append(flight_data.dep_delay)
            if flight_data.arr_delay is not None:
                arr_delays.append(flight_data.arr_delay)
                # Count on-time (arrival delay <= 15 minutes)
                if flight_data.arr_delay <= ON_TIME_THRESHOLD:
                    on_time_count += 1
        
        # Calculate averages
        avg_dep_delay = sum(dep_delays) / len(dep_delays) if dep_delays else None
        avg_arr_delay = sum(arr_delays) / len(arr_delays) if arr_delays else None
        
        # Use arrival delay as primary, fallback to departure delay
        avg_delay = avg_arr_delay if avg_arr_delay is not None else avg_dep_delay
        
        # Calculate on-time percentage
        on_time_percentage = (on_time_count / len(arr_delays) * 100) if arr_delays else None
        
        # Get sample period (date range from CSV)
        from datetime import date
        dates = [(f.year, f.month, f.day) for f in matching_flights]
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            sample_start = date(min_date[0], min_date[1], min_date[2])
            sample_end = date(max_date[0], max_date[1], max_date[2])
        else:
            sample_start = None
            sample_end = None
        
        # Calculate categories
        delay_category = "UNKNOWN"
        if avg_delay is not None:
            if avg_delay <= 5:
                delay_category = "EXCELLENT"
            elif avg_delay <= 15:
                delay_category = "GOOD"
            elif avg_delay <= 30:
                delay_category = "FAIR"
            else:
                delay_category = "POOR"
        
        on_time_category = "UNKNOWN"
        if on_time_percentage is not None:
            if on_time_percentage >= 90:
                on_time_category = "EXCELLENT"
            elif on_time_percentage >= 80:
                on_time_category = "GOOD"
            elif on_time_percentage >= 70:
                on_time_category = "FAIR"
            else:
                on_time_category = "POOR"
        
        return HistoricalBaselineResponse(
            route_key=route_key,
            airline_code=airline_code,
            avg_delay_minutes=avg_delay,
            on_time_percentage=on_time_percentage,
            total_flights=total_flights,
            avg_departure_delay=avg_dep_delay,
            avg_arrival_delay=avg_arr_delay,
            sample_period_start=sample_start,
            sample_period_end=sample_end,
            delay_category=delay_category,
            on_time_category=on_time_category,
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
        
        # Determine data source (CSV or mock)
        # Check if flight exists in CSV by trying to look it up
        is_mock = False
        data_source = "csv"
        
        # Heuristic: if route is one of the mock routes, it's likely mock data
        if flight.origin_icao and flight.destination_icao:
            mock_routes = [("KSFO", "KJFK"), ("KJFK", "EGLL"), ("KLAX", "RJAA"), 
                          ("KORD", "KLAX"), ("EGLL", "OMDB"), ("WMKK", "WSSS"), ("VABB", "OMDB")]
            if (flight.origin_icao, flight.destination_icao) in mock_routes:
                is_mock = True
                data_source = "mock"
            else:
                # Try to verify it's in CSV
                csv_flight = self.csv_service.find_flight_by_full_number(flight.flight_number)
                if not csv_flight:
                    is_mock = True
                    data_source = "mock"
                else:
                    data_source = "csv"
        else:
            # No route info, likely mock
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
