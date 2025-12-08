"""
Mock Data Generator

Generates realistic synthetic flight data when live data is unavailable.
"""

import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

from services.opensky_client import FlightState, FlightRoute, AircraftMetadata, get_airline_info

class MockDataGenerator:
    """Generates synthetic flight data for demonstration purposes."""
    
    # Common US Routes for simulation
    ROUTES = [
        {"origin": "KSFO", "dest": "KJFK", "duration": 320},  # SFO -> JFK (5h 20m)
        {"origin": "KJFK", "dest": "EGLL", "duration": 420},  # JFK -> LHR (7h)
        {"origin": "KLAX", "dest": "RJAA", "duration": 660},  # LAX -> NRT (11h)
        {"origin": "KORD", "dest": "KLAX", "duration": 260},  # ORD -> LAX (4h 20m)
        {"origin": "EGLL", "dest": "OMDB", "duration": 410},  # LHR -> DXB (6h 50m)
        {"origin": "WMKK", "dest": "WSSS", "duration": 60},   # KUL -> SIN (1h)
        {"origin": "VABB", "dest": "OMDB", "duration": 200},  # BOM -> DXB (3h 20m)
    ]
    
    def generate_mock_state(self, flight_number: str) -> FlightState:
        """Generate a synthetic FlightState representing an airborne aircraft."""
        base_route = random.choice(self.ROUTES)
        
        # Simulate being mid-flight
        return FlightState(
            icao24=self._generate_icao24(flight_number),
            callsign=flight_number.upper(),
            origin_country="United States",
            time_position=int(datetime.now().timestamp()),
            last_contact=int(datetime.now().timestamp()),
            longitude=-95.7129 + random.uniform(-10, 10), # Random over US
            latitude=37.0902 + random.uniform(-5, 5),
            baro_altitude=30000.0 + random.uniform(-2000, 2000),
            on_ground=False,
            velocity=250.0 + random.uniform(-20, 20),
            true_track=90.0 + random.uniform(-10, 10),
            vertical_rate=0.0,
            sensors=None,
            geo_altitude=30000.0,
            squawk="1234",
            spi=False,
            position_source=0
        )

    def generate_mock_route(self, flight_number: str) -> FlightRoute:
        """Generate a matching synthetic route."""
        # Pick route based on hash of flight number for consistency
        idx = hash(flight_number) % len(self.ROUTES)
        route_data = self.ROUTES[idx]
        
        return FlightRoute(
            callsign=flight_number.upper(),
            departure_airport=route_data["origin"],
            arrival_airport=route_data["dest"],
            operator_icao=flight_number[:3]
        )
        
    def generate_mock_aircraft(self, icao24: str) -> AircraftMetadata:
        """Generate synthetic aircraft metadata."""
        manufacturers = ["Boeing", "Airbus"]
        models = ["737-800", "777-300ER", "A320neo", "A350-900"]
        
        return AircraftMetadata(
            icao24=icao24,
            registration=f"N{random.randint(100,999)}A",
            manufacturer=random.choice(manufacturers),
            model=random.choice(models),
            type_code="L2J",
            serial_number=str(random.randint(10000, 99999)),
            operator="Mock Airlines",
            first_flight_date="2018-01-01"
        )
        
    def generate_schedule(self, flight_number: str) -> Tuple[datetime, datetime]:
        """Generate realistic schedule (dep, arr) based on current time."""
        # Assume flight departed 1-3 hours ago for "active" look
        now = datetime.now()
        
        # Get route duration used in generate_mock_route
        idx = hash(flight_number) % len(self.ROUTES)
        duration_mins = self.ROUTES[idx]["duration"]
        
        scheduled_dep = now - timedelta(minutes=random.randint(30, 180))
        scheduled_arr = scheduled_dep + timedelta(minutes=duration_mins)
        
        return scheduled_dep, scheduled_arr

    def generate_mock_events(self, scheduled_dep: datetime) -> list[dict]:
        """Generate a sequence of synthetic events based on schedule."""
        events = []
        
        # 1. Scheduled
        events.append({
            "event_type": "SCHEDULED",
            "timestamp": scheduled_dep - timedelta(hours=24),
            "actor": "SCHEDULING_SYSTEM",
            "payload": {"scheduled_departure": scheduled_dep.isoformat()}
        })
        
        # 2. Check-in Open
        events.append({
            "event_type": "CHECK_IN_OPEN",
            "timestamp": scheduled_dep - timedelta(hours=3),
            "actor": "AIRPORT_SYSTEM",
            "payload": {}
        })
        
        # 3. Gate Assigned
        gate = f"{random.choice(['A','B','C'])}{random.randint(1,99)}"
        events.append({
            "event_type": "GATE_ASSIGNED",
            "timestamp": scheduled_dep - timedelta(hours=2),
            "actor": "AIRPORT_OPS",
            "payload": {"gate": gate}
        })
        
        # 4. Boarding
        events.append({
            "event_type": "BOARDING_OPEN",
            "timestamp": scheduled_dep - timedelta(minutes=45),
            "actor": "GATE_AGENT",
            "payload": {"gate": gate}
        })
        
        # 5. Departure (slightly late to show detail)
        actual_dep = scheduled_dep + timedelta(minutes=random.randint(-5, 10))
        events.append({
            "event_type": "PUSHBACK",
            "timestamp": actual_dep,
            "actor": "PILOT",
            "payload": {}
        })
        
        events.append({
            "event_type": "TAKEOFF",
            "timestamp": actual_dep + timedelta(minutes=15),
            "actor": "ATC_TOWER",
            "payload": {"runway": f"{random.randint(1,36)}L"}
        })
        
        return events

    def _generate_icao24(self, seed: str) -> str:
        """Generate consistent fake hex ID."""
        h = hash(seed)
        return hex(h)[-6:].replace('x', '0')
