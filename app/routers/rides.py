from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter()

def _available_seats(ride: models.Ride) -> int:
    booked = sum(
        1 for r in ride.reservations
        if r.status != models.ReservationStatus.cancelled
    )
    return ride.bus.total_seats - booked

@router.get("/", response_model=List[schemas.RideOut])
def list_rides(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """List all scheduled and active rides."""
    rides = db.query(models.Ride).filter(
        models.Ride.status.in_([
            models.RideStatus.scheduled,
            models.RideStatus.active,
        ])
    ).all()
    result = []
    for ride in rides:
        out = schemas.RideOut(
            id=ride.id,
            status=ride.status,
            departure_time=ride.departure_time,
            available_seats=_available_seats(ride),
            total_seats=ride.bus.total_seats,
            current_lat=ride.current_lat,
            current_lng=ride.current_lng,
            location_updated_at=ride.location_updated_at,
            route=ride.route,
        )
        result.append(out)
    return result

@router.get("/{ride_id}", response_model=schemas.RideOut)
def get_ride(ride_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Poll this endpoint every 5s to get updated bus location."""
    ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(404, "Ride not found")
    return schemas.RideOut(
        id=ride.id,
        status=ride.status,
        departure_time=ride.departure_time,
        available_seats=_available_seats(ride),
        total_seats=ride.bus.total_seats,
        current_lat=ride.current_lat,
        current_lng=ride.current_lng,
        location_updated_at=ride.location_updated_at,
        route=ride.route,
    )