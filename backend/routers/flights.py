"""
Flights Router

API endpoints for flight search, events, and delay analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from schemas.flight import FlightResponse, FlightSearchResponse
from schemas.event import EventWithVerification
from schemas.delay import DelayAnalysisResponse
from schemas.historical import HistoricalBaselineResponse
from services.flight_service import FlightService
from services.event_assembler import EventAssembler
from services.delay_analyzer import DelayAnalyzer

router = APIRouter()


@router.get(
    "/search-flight/{flight_number}",
    response_model=FlightSearchResponse,
    summary="Search for a flight",
    description="Search for a flight by its flight number. Returns flight details with current status."
)
async def search_flight(
    flight_number: str,
    db: Session = Depends(get_db)
):
    """
    Search for a flight by flight number.
    
    - **flight_number**: The flight number to search for (e.g., UA123, AA456)
    
    Returns flight details including origin, destination, schedule, and current status.
    """
    try:
        service = FlightService(db)
        
        # Try to find in database first
        flight = service.get_flight_by_number(flight_number.upper())
        
        if flight:
            return FlightSearchResponse(
                found=True,
                flight=service.to_response(flight),
                message="Flight found in database"
            )
        
        # Try to fetch from OpenSky
        try:
            flight = await service.fetch_and_create_flight(flight_number.upper())
        except Exception as e:
            # Log the error but don't crash
            print(f"Error fetching flight from OpenSky: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return not found instead of crashing
            return FlightSearchResponse(
                found=False,
                flight=None,
                message=f"Error fetching flight data: {str(e)}"
            )
        
        if flight:
            return FlightSearchResponse(
                found=True,
                flight=service.to_response(flight),
                message="Flight data fetched from OpenSky Network"
            )
        
        return FlightSearchResponse(
            found=False,
            flight=None,
            message=f"No flight found for {flight_number.upper()}"
        )
    except Exception as e:
        # Catch all other errors
        print(f"Error in search_flight: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@router.get(
    "/search-flight/trace/{flight_number}",
    response_model=list[dict],
    summary="Trace flight on blockchain",
    description="Perform a transparent search on the Ethereum blockchain first, returning a log of steps."
)
async def trace_flight_search(
    flight_number: str,
    db: Session = Depends(get_db)
):
    """
    Trace flight search steps on blockchain.
    
    Returns a list of log entries describing the lookup process on the smart contract.
    """
    from services.blockchain_service import BlockchainService
    from services.mock_data_generator import MockDataGenerator
    
    bc_service = BlockchainService(db)
    flight_number = flight_number.upper()
    
    # 1. Search Chain
    logs = await bc_service.search_flight_events_on_chain(flight_number)
    
    # Check if we found events
    found_events = False
    for log in logs:
        if "Found" in log.get("message", "") and "records" in log.get("message", ""):
            found_events = True
            break
            
    if found_events:
        return logs
        
    # 2. If Not Found -> Activate Oracle / Mock Generator
    logs.append({"type": "warning", "message": f"Flight {flight_number} not indexed on-chain."})
    logs.append({"type": "info", "message": "Activating FlightChain Oracle Service..."})
    
    # Create Flight (Service already handles mock gen)
    f_service = FlightService(db)
    flight = await f_service.fetch_and_create_flight(flight_number)
    
    if not flight:
        logs.append({"type": "error", "message": "Oracle failed to retrieve flight data."})
        return logs
        
    logs.append({"type": "success", "message": f"Oracle retrieved metadata for {flight.airline_name} {flight_number}."})
    
    # Generate Events
    mock_gen = MockDataGenerator()
    # Ensure we have a scheduled_departure for event generation
    if not flight.scheduled_departure:
         # Fallback default - create a fresh datetime object
         scheduled_dep_for_events = datetime.now()
    else:
         scheduled_dep_for_events = flight.scheduled_departure
         
    events_data = mock_gen.generate_mock_events(scheduled_dep_for_events)
    
    assembler = EventAssembler(db)
    logs.append({"type": "info", "message": f"Assembling {len(events_data)} verified flight events..."})
    
    for evt_data in events_data:
        # Create in DB only (blockchain write happens via MetaMask in frontend)
        evt = assembler.create_event(
            flight_id=flight.id,
            event_type=evt_data["event_type"],
            timestamp=evt_data["timestamp"],
            actor=evt_data["actor"],
            payload=evt_data["payload"]
        )
        
        logs.append({"type": "data", "message": f"Event '{evt.event_type}' created in database. Ready for blockchain recording via MetaMask."})

    logs.append({"type": "success", "message": f"Flight indexing complete. {len(events_data)} events ready for blockchain recording."})
    logs.append({"type": "info", "message": "MetaMask will prompt you to record events on blockchain."})
    
    return logs


@router.get(
    "/flight/{flight_id}",
    response_model=FlightResponse,
    summary="Get flight details",
    description="Get detailed information for a specific flight by ID."
)
async def get_flight(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """Get flight details by ID."""
    service = FlightService(db)
    flight = service.get_flight_by_id(flight_id)
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    return service.to_response(flight)


@router.get(
    "/flight/{flight_id}/events",
    response_model=list[EventWithVerification],
    summary="Get flight events",
    description="Get all events for a flight with blockchain verification status."
)
async def get_flight_events(
    flight_id: int,
    include_payload: bool = Query(False, description="Include raw event payload"),
    db: Session = Depends(get_db)
):
    """
    Get all events for a flight.
    
    Returns events with blockchain verification status showing whether
    each event has been verified on-chain.
    """
    assembler = EventAssembler(db)
    events = assembler.get_events_with_verification(flight_id)
    
    if not events:
        # Check if flight exists
        service = FlightService(db)
        if not service.get_flight_by_id(flight_id):
            raise HTTPException(status_code=404, detail="Flight not found")
    
    return events


@router.get(
    "/flight/{flight_id}/delay-analysis",
    response_model=DelayAnalysisResponse,
    summary="Get delay analysis",
    description="Get automated delay analysis with human-readable explanations."
)
async def get_delay_analysis(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """
    Analyze delays for a flight.
    
    Uses event timestamps and flight schedule to derive delay reasons
    and provide a human-readable explanation.
    """
    service = FlightService(db)
    flight = service.get_flight_by_id(flight_id)
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    analyzer = DelayAnalyzer(db)
    return analyzer.analyze(flight)


@router.get(
    "/flight/{flight_id}/historical-baseline",
    response_model=HistoricalBaselineResponse,
    summary="Get historical performance",
    description="Get historical performance baseline for this flight's route."
)
async def get_historical_baseline(
    flight_id: int,
    db: Session = Depends(get_db)
):
    """
    Get historical performance data for the flight's route.
    
    Returns average delays, on-time percentage, and performance trends
    based on historical data for the same route.
    """
    service = FlightService(db)
    flight = service.get_flight_by_id(flight_id)
    
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    baseline = service.get_historical_baseline(flight)
    
    if not baseline:
        return HistoricalBaselineResponse(
            route_key=flight.route_key,
            airline_code=flight.airline_code,
            avg_delay_minutes=None,
            on_time_percentage=None,
            total_flights=0
        )
    
    return baseline


@router.get(
    "/aircraft/{icao24}",
    summary="Get aircraft metadata",
    description="Get aircraft information by ICAO24 address."
)
async def get_aircraft(
    icao24: str,
    db: Session = Depends(get_db)
):
    """Get aircraft metadata by ICAO24 address."""
    service = FlightService(db)
    aircraft = service.get_aircraft_by_icao24(icao24)
    
    if not aircraft:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    
    return aircraft
