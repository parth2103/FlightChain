"""
CSV Flight Data Service

Service for loading and querying flight data from CSV file.
Replaces OpenSky API integration with CSV-based data source.
"""

import csv
import math
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from functools import lru_cache
from dataclasses import dataclass

from config import settings


@dataclass
class CSVFlightData:
    """Represents flight data from CSV."""
    id: int
    year: int
    month: int
    day: int
    carrier: str
    flight: str
    tailnum: Optional[str]
    origin: str
    dest: str
    sched_dep_time: Optional[float]
    dep_time: Optional[float]
    sched_arr_time: Optional[float]
    arr_time: Optional[float]
    dep_delay: Optional[float]
    arr_delay: Optional[float]
    air_time: Optional[float]
    distance: Optional[float]
    airline_name: str
    time_hour: str


class CSVFlightService:
    """Service for querying flight data from CSV file."""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize CSV flight service.
        
        Args:
            csv_path: Path to flights.csv file. If None, will search for it.
        """
        self.csv_path = csv_path or self._find_csv_file()
        self._flights_cache: Dict[str, List[CSVFlightData]] = {}
        self._loaded = False
        
    def _find_csv_file(self) -> Path:
        """Find the flights.csv file in common locations."""
        # Check current directory (project root)
        root_path = Path(__file__).parent.parent.parent / "flights.csv"
        if root_path.exists():
            return root_path
        
        # Check backend directory
        backend_path = Path(__file__).parent.parent / "flights.csv"
        if backend_path.exists():
            return backend_path
        
        # Check config override
        if hasattr(settings, 'csv_flights_path') and settings.csv_flights_path:
            config_path = Path(settings.csv_flights_path)
            if config_path.exists():
                return config_path
        
        # Default to project root
        return Path(__file__).parent.parent.parent / "flights.csv"
    
    def _load_flights(self) -> None:
        """Load flights from CSV file into memory cache."""
        if self._loaded:
            return
        
        if not self.csv_path.exists():
            print(f"⚠️  Warning: CSV file not found at {self.csv_path}")
            print("   Falling back to mock data generator for flights.")
            self._loaded = True
            return
        
        print(f"Loading flight data from {self.csv_path}...")
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row_count = 0
                
                for row in reader:
                    try:
                        # Parse flight data
                        carrier = row.get('carrier', '').strip()
                        flight = row.get('flight', '').strip()
                        
                        if not carrier or not flight:
                            continue
                        
                        # Create key for lookup: "UA1545"
                        key = f"{carrier}{flight}"
                        
                        # Parse numeric fields
                        flight_id = int(row.get('id', 0))
                        year = int(row.get('year', 2013))
                        month = int(row.get('month', 1))
                        day = int(row.get('day', 1))
                        
                        # Parse optional float fields
                        def safe_float(val):
                            if val == '' or val is None:
                                return None
                            try:
                                return float(val)
                            except (ValueError, TypeError):
                                return None
                        
                        sched_dep_time = safe_float(row.get('sched_dep_time'))
                        dep_time = safe_float(row.get('dep_time'))
                        sched_arr_time = safe_float(row.get('sched_arr_time'))
                        arr_time = safe_float(row.get('arr_time'))
                        dep_delay = safe_float(row.get('dep_delay'))
                        arr_delay = safe_float(row.get('arr_delay'))
                        air_time = safe_float(row.get('air_time'))
                        distance = safe_float(row.get('distance'))
                        
                        flight_data = CSVFlightData(
                            id=flight_id,
                            year=year,
                            month=month,
                            day=day,
                            carrier=carrier,
                            flight=flight,
                            tailnum=row.get('tailnum') if row.get('tailnum') else None,
                            origin=row.get('origin', '').strip(),
                            dest=row.get('dest', '').strip(),
                            sched_dep_time=sched_dep_time,
                            dep_time=dep_time,
                            sched_arr_time=sched_arr_time,
                            arr_time=arr_time,
                            dep_delay=dep_delay,
                            arr_delay=arr_delay,
                            air_time=air_time,
                            distance=distance,
                            airline_name=row.get('name', '').strip(),
                            time_hour=row.get('time_hour', '')
                        )
                        
                        # Add to cache (multiple rows per flight possible)
                        if key not in self._flights_cache:
                            self._flights_cache[key] = []
                        self._flights_cache[key].append(flight_data)
                        
                        row_count += 1
                        
                        # Progress indicator for large files
                        if row_count % 50000 == 0:
                            print(f"  Loaded {row_count} flights...")
                    
                    except (ValueError, KeyError) as e:
                        # Skip invalid rows
                        continue
                
                print(f"✓ Loaded {row_count} flights from CSV")
                print(f"✓ Indexed {len(self._flights_cache)} unique flights")
                
        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
            import traceback
            traceback.print_exc()
        
        self._loaded = True
    
    def csv_time_to_datetime(self, year: int, month: int, day: int, time_decimal: Optional[float], use_current_date: bool = True) -> Optional[datetime]:
        """
        Convert CSV time format to datetime.
        
        CSV times are in HHMM format where:
        - 515 = 5:15 AM (5 hours, 15 minutes)
        - 517.0 = 5:17 AM
        - 830 = 8:30 AM
        - 1430 = 14:30 (2:30 PM)
        - 2359 = 23:59 (11:59 PM)
        
        Format: HHMM where HH is hours (0-23) and MM is minutes (00-59)
        
        Args:
            year: Year from CSV (historical date, will be replaced if use_current_date=True)
            month: Month from CSV
            day: Day from CSV
            time_decimal: Time in HHMM format (e.g., 515.0 for 5:15 AM, 1430 for 2:30 PM)
            use_current_date: If True, use today's date instead of historical date
        
        Returns:
            datetime object with current date (if use_current_date=True) or None if invalid
        """
        if time_decimal is None or math.isnan(time_decimal):
            return None
        
        try:
            # Convert to integer to get HHMM format
            # e.g., 515.0 -> 515 -> hours=5, minutes=15
            # e.g., 830.0 -> 830 -> hours=8, minutes=30
            # e.g., 1430.0 -> 1430 -> hours=14, minutes=30
            time_value = int(float(time_decimal))
            
            # Extract hours and minutes from HHMM format
            hours = time_value // 100  # First 1-2 digits (hours)
            minutes = time_value % 100  # Last 2 digits (minutes)
            
            # Validate hours (should be 0-23)
            if hours < 0 or hours > 23:
                return None
            
            # Validate minutes (should be 0-59)
            if minutes < 0 or minutes > 59:
                return None
            
            # Use current date instead of historical date
            if use_current_date:
                now = datetime.now()
                result_date = datetime(now.year, now.month, now.day, hours, minutes, 0)
            else:
                result_date = datetime(year, month, day, hours, minutes, 0)
            
            return result_date
        except (ValueError, TypeError, OverflowError) as e:
            print(f"Error converting time {time_decimal}: {e}")
            return None
    
    def find_flight(self, carrier: str, flight_number: str) -> Optional[CSVFlightData]:
        """
        Find a flight by carrier and flight number.
        
        Args:
            carrier: Airline carrier code (e.g., "UA")
            flight_number: Flight number (e.g., "1545")
        
        Returns:
            CSVFlightData or None if not found
        """
        self._load_flights()
        
        # Normalize input
        carrier = carrier.upper().strip()
        flight_number = str(flight_number).strip()
        
        # Create lookup key
        key = f"{carrier}{flight_number}"
        
        # Find matching flights
        matching_flights = self._flights_cache.get(key, [])
        
        if not matching_flights:
            return None
        
        # Return the most recent flight (highest id, which corresponds to later dates)
        # Sort by id descending to get most recent
        sorted_flights = sorted(matching_flights, key=lambda f: f.id, reverse=True)
        return sorted_flights[0]
    
    def find_flight_by_full_number(self, full_flight_number: str) -> Optional[CSVFlightData]:
        """
        Find a flight by full flight number (e.g., "UA1545").
        
        Attempts to parse carrier and flight number from the input.
        
        Args:
            full_flight_number: Full flight number (e.g., "UA1545", "UA 1545")
        
        Returns:
            CSVFlightData or None if not found
        """
        full_flight_number = full_flight_number.upper().strip()
        
        # Try different parsing strategies
        # Strategy 1: Direct match (e.g., "UA1545")
        if len(full_flight_number) >= 2:
            # Common carriers are 2 letters
            for carrier_len in [2, 3]:
                if len(full_flight_number) > carrier_len:
                    carrier = full_flight_number[:carrier_len]
                    flight = full_flight_number[carrier_len:]
                    result = self.find_flight(carrier, flight)
                    if result:
                        return result
        
        # Strategy 2: Split by space (e.g., "UA 1545")
        parts = full_flight_number.split()
        if len(parts) >= 2:
            carrier = parts[0]
            flight = ''.join(parts[1:])
            result = self.find_flight(carrier, flight)
            if result:
                return result
        
        return None
    
    def get_airline_name(self, carrier: str) -> Optional[str]:
        """Get airline name for a carrier code."""
        self._load_flights()
        
        # Find any flight with this carrier and return its airline name
        for key, flights in self._flights_cache.items():
            if flights and flights[0].carrier == carrier.upper():
                return flights[0].airline_name
        
        return None

