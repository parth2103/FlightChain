"""
Delay Analyzer Service

Service for analyzing flight delays and generating human-readable explanations.
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from models.flight import Flight
from models.event import FlightEvent, EventTypes
from schemas.delay import (
    DelayAnalysisResponse,
    DelayReason,
    DelayCategory,
    DelayType,
    categorize_delay,
)


class DelayAnalyzer:
    """
    Analyzes flight delays based on event timestamps and flight schedule.
    
    Uses event patterns to derive probable delay causes and generates
    human-readable explanations.
    """
    
    # On-time threshold in minutes
    ON_TIME_THRESHOLD = 15
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze(self, flight: Flight) -> DelayAnalysisResponse:
        """
        Perform comprehensive delay analysis for a flight.
        
        Args:
            flight: Flight to analyze
            
        Returns:
            DelayAnalysisResponse with breakdown and explanation
        """
        # Get departure delay
        departure_delay = self._calculate_departure_delay(flight)
        
        # Get arrival delay
        arrival_delay = self._calculate_arrival_delay(flight)
        
        # Determine total delay (use arrival if available, else departure)
        total_delay = arrival_delay if arrival_delay is not None else (departure_delay or 0)
        
        # Determine if delayed
        is_delayed = total_delay > self.ON_TIME_THRESHOLD
        
        # Get events for pattern analysis
        events = self._get_flight_events(flight.id)
        
        # Analyze delay reasons
        reasons = self._derive_reasons(flight, events, departure_delay, arrival_delay)
        
        # Generate human-readable explanation
        human_readable = self._generate_explanation(flight, reasons, total_delay)
        
        return DelayAnalysisResponse(
            flight_id=flight.id,
            flight_number=flight.flight_number,
            is_delayed=is_delayed,
            total_delay_minutes=max(0, total_delay),
            category=categorize_delay(total_delay),
            departure_delay_minutes=departure_delay,
            arrival_delay_minutes=arrival_delay,
            reasons=reasons,
            human_readable=human_readable,
            on_time_threshold_minutes=self.ON_TIME_THRESHOLD,
        )
    
    def _calculate_departure_delay(self, flight: Flight) -> Optional[float]:
        """Calculate departure delay in minutes."""
        if flight.actual_departure and flight.scheduled_departure:
            delta = flight.actual_departure - flight.scheduled_departure
            return delta.total_seconds() / 60
        return None
    
    def _calculate_arrival_delay(self, flight: Flight) -> Optional[float]:
        """Calculate arrival delay in minutes."""
        if flight.actual_arrival and flight.scheduled_arrival:
            delta = flight.actual_arrival - flight.scheduled_arrival
            return delta.total_seconds() / 60
        return None
    
    def _get_flight_events(self, flight_id: int) -> list[FlightEvent]:
        """Get all events for a flight."""
        return (
            self.db.query(FlightEvent)
            .filter(FlightEvent.flight_id == flight_id)
            .order_by(FlightEvent.timestamp)
            .all()
        )
    
    def _derive_reasons(
        self,
        flight: Flight,
        events: list[FlightEvent],
        departure_delay: Optional[float],
        arrival_delay: Optional[float]
    ) -> list[DelayReason]:
        """
        Derive delay reasons from flight data and events.
        
        Uses event patterns and timing to identify probable causes.
        """
        reasons = []
        
        # Late departure analysis
        if departure_delay and departure_delay > self.ON_TIME_THRESHOLD:
            reasons.append(DelayReason(
                type=DelayType.DEPARTURE_DELAY,
                minutes=departure_delay,
                explanation=f"Flight departed {int(departure_delay)} minutes after scheduled time",
                confidence=0.95
            ))
            
            # Check for delay announcement events
            delay_events = [e for e in events if e.event_type == EventTypes.DELAY_ANNOUNCED]
            if delay_events:
                # Extract reason from payload if available
                for event in delay_events:
                    if event.payload and "reason" in event.payload:
                        reason_type = self._map_reason_to_type(event.payload["reason"])
                        reasons.append(DelayReason(
                            type=reason_type,
                            minutes=departure_delay,
                            explanation=event.payload.get("reason", "Delay announced"),
                            confidence=0.9
                        ))
            else:
                # Infer reason from event patterns
                inferred = self._infer_delay_reason(events, flight)
                if inferred:
                    reasons.append(inferred)
        
        # Gate delay analysis
        gate_delay = self._calculate_gate_delay(events, flight)
        if gate_delay and gate_delay > 10:
            reasons.append(DelayReason(
                type=DelayType.GATE_DELAY,
                minutes=gate_delay,
                explanation=f"Extended time at gate ({int(gate_delay)} minutes beyond normal)",
                confidence=0.7
            ))
        
        # Taxi delay analysis
        taxi_delay = self._calculate_taxi_delay(events)
        if taxi_delay and taxi_delay > 20:
            reasons.append(DelayReason(
                type=DelayType.TAXI_DELAY,
                minutes=taxi_delay - 15,  # Subtract normal taxi time
                explanation=f"Extended taxi time ({int(taxi_delay)} minutes)",
                confidence=0.8
            ))
        
        # Airborne delay (if arrival delay > departure delay)
        if departure_delay is not None and arrival_delay is not None:
            airborne_delay = arrival_delay - departure_delay
            if airborne_delay > 15:
                reasons.append(DelayReason(
                    type=DelayType.AIRBORNE_DELAY,
                    minutes=airborne_delay,
                    explanation=f"Additional {int(airborne_delay)} minutes in flight (possible rerouting or holding pattern)",
                    confidence=0.6
                ))
        
        return reasons
    
    def _infer_delay_reason(
        self,
        events: list[FlightEvent],
        flight: Flight
    ) -> Optional[DelayReason]:
        """Infer delay reason from event patterns when no explicit reason given."""
        
        # Check for late boarding
        boarding_events = [e for e in events if e.event_type in [
            EventTypes.BOARDING_OPEN, EventTypes.BOARDING_CLOSED
        ]]
        
        if boarding_events and flight.scheduled_departure:
            last_boarding = max(boarding_events, key=lambda e: e.timestamp)
            time_before_scheduled = (flight.scheduled_departure - last_boarding.timestamp).total_seconds() / 60
            
            if time_before_scheduled < 0:
                return DelayReason(
                    type=DelayType.GATE_DELAY,
                    minutes=abs(time_before_scheduled),
                    explanation="Boarding completed after scheduled departure time",
                    confidence=0.7
                )
        
        # Check for gate change (can cause delays)
        gate_changes = [e for e in events if e.event_type == EventTypes.GATE_CHANGE]
        if gate_changes:
            return DelayReason(
                type=DelayType.GATE_DELAY,
                minutes=15,  # Estimated impact
                explanation="Gate change may have contributed to delay",
                confidence=0.5
            )
        
        return None
    
    def _calculate_gate_delay(
        self,
        events: list[FlightEvent],
        flight: Flight
    ) -> Optional[float]:
        """Calculate excess time spent at gate."""
        pushback_event = next(
            (e for e in events if e.event_type == EventTypes.PUSHBACK),
            None
        )
        
        if pushback_event and flight.scheduled_departure:
            # Normal time between scheduled and pushback is ~10 min
            delay = (pushback_event.timestamp - flight.scheduled_departure).total_seconds() / 60
            if delay > 10:
                return delay - 10  # Excess beyond normal
        
        return None
    
    def _calculate_taxi_delay(self, events: list[FlightEvent]) -> Optional[float]:
        """Calculate taxi time."""
        taxi_start = next(
            (e for e in events if e.event_type == EventTypes.TAXI_OUT),
            None
        )
        takeoff = next(
            (e for e in events if e.event_type == EventTypes.TAKEOFF),
            None
        )
        
        if taxi_start and takeoff:
            return (takeoff.timestamp - taxi_start.timestamp).total_seconds() / 60
        
        return None
    
    def _map_reason_to_type(self, reason_text: str) -> DelayType:
        """Map text reason to DelayType enum."""
        reason_lower = reason_text.lower()
        
        if "weather" in reason_lower:
            return DelayType.WEATHER_DELAY
        elif "atc" in reason_lower or "traffic" in reason_lower:
            return DelayType.ATC_DELAY
        elif "mechanical" in reason_lower or "maintenance" in reason_lower:
            return DelayType.MECHANICAL_DELAY
        elif "crew" in reason_lower:
            return DelayType.CREW_DELAY
        elif "connect" in reason_lower or "passenger" in reason_lower:
            return DelayType.CONNECTING_DELAY
        
        return DelayType.DEPARTURE_DELAY
    
    def _generate_explanation(
        self,
        flight: Flight,
        reasons: list[DelayReason],
        total_delay: float
    ) -> str:
        """Generate human-readable delay explanation."""
        if total_delay <= 0:
            return f"Flight {flight.flight_number} departed and arrived on time."
        
        if total_delay <= self.ON_TIME_THRESHOLD:
            return f"Flight {flight.flight_number} experienced a minor delay of {int(total_delay)} minutes, which is within acceptable on-time performance."
        
        # Build explanation from reasons
        if not reasons:
            return f"Flight {flight.flight_number} was delayed by {int(total_delay)} minutes. The specific cause could not be determined from available data."
        
        # Use the highest confidence reason as primary
        reasons_sorted = sorted(reasons, key=lambda r: r.confidence or 0, reverse=True)
        primary_reason = reasons_sorted[0]
        
        explanation = f"Flight {flight.flight_number} experienced a {int(total_delay)}-minute delay. "
        explanation += primary_reason.explanation + "."
        
        # Add secondary reasons if confidence is high enough
        secondary = [r for r in reasons_sorted[1:] if (r.confidence or 0) > 0.6]
        if secondary:
            explanation += " Contributing factors may include: "
            explanation += "; ".join([r.explanation for r in secondary[:2]]) + "."
        
        return explanation
