from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.auth import require_driver

router = APIRouter()

@router.get("/ride/{ride_id}/passengers", response_model=List[schemas.PassengerListItem])
def get_passengers(
    ride_id: int,
    db: Session = Depends(get_db),
    driver: models.User = Depends(require_driver),
):
    """Poll this every 5s to refresh the passenger list."""
    ride = db.query(models.Ride).filter(
        models.Ride.id == ride_id,
        models.Ride.driver_id == driver.id,
    ).first()
    if not ride:
        raise HTTPException(404, "Ride not found")
    return [
        schemas.PassengerListItem(
            reservation_id=r.id,
            passenger_name=r.user.name,
            seat_number=r.seat_number,
            status=r.status,
        )
        for r in ride.reservations
        if r.status != models.ReservationStatus.cancelled
    ]

@router.post("/ride/{ride_id}/start")
def start_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    driver: models.User = Depends(require_driver),
):
    ride = db.query(models.Ride).filter(
        models.Ride.id == ride_id,
        models.Ride.driver_id == driver.id,
    ).first()
    if not ride:
        raise HTTPException(404, "Ride not found")
    if ride.status != models.RideStatus.scheduled:
        raise HTTPException(400, f"Ride is already {ride.status}")
    ride.status = models.RideStatus.active
    ride.started_at = datetime.utcnow()
    db.commit()
    return {"message": "Ride started", "ride_id": ride_id}

@router.post("/ride/{ride_id}/stop")
def stop_ride(
    ride_id: int,
    db: Session = Depends(get_db),
    driver: models.User = Depends(require_driver),
):
    ride = db.query(models.Ride).filter(
        models.Ride.id == ride_id,
        models.Ride.driver_id == driver.id,
    ).first()
    if not ride:
        raise HTTPException(404, "Ride not found")
    if ride.status != models.RideStatus.active:
        raise HTTPException(400, "Ride is not active")
    ride.status = models.RideStatus.completed
    ride.ended_at = datetime.utcnow()
    db.commit()
    return {"message": "Ride completed", "ride_id": ride_id}

@router.post("/ride/{ride_id}/location")
def update_location(
    ride_id: int,
    payload: schemas.LocationUpdate,
    db: Session = Depends(get_db),
    driver: models.User = Depends(require_driver),
):
    """Driver app calls this every 5s with GPS coordinates."""
    ride = db.query(models.Ride).filter(
        models.Ride.id == ride_id,
        models.Ride.driver_id == driver.id,
        models.Ride.status == models.RideStatus.active,
    ).first()
    if not ride:
        raise HTTPException(404, "Active ride not found")
    ride.current_lat = payload.latitude
    ride.current_lng = payload.longitude
    ride.location_updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Location updated"}

@router.post("/ride/{ride_id}/confirm")
def confirm_passenger(
    ride_id: int,
    payload: schemas.ConfirmPassengerRequest,
    db: Session = Depends(get_db),
    driver: models.User = Depends(require_driver),
):
    """Driver enters the passenger's 2-digit code to confirm boarding."""
    ride = db.query(models.Ride).filter(
        models.Ride.id == ride_id,
        models.Ride.driver_id == driver.id,
    ).first()
    if not ride:
        raise HTTPException(404, "Ride not found")

    reservation = db.query(models.Reservation).filter(
        models.Reservation.ride_id == ride_id,
        models.Reservation.confirmation_code == payload.code,
        models.Reservation.status == models.ReservationStatus.pending,
    ).first()
    if not reservation:
        raise HTTPException(404, "Code not found or already confirmed")

    reservation.status = models.ReservationStatus.confirmed
    reservation.confirmed_at = datetime.utcnow()
    db.commit()
    return {
        "message": "Passenger confirmed",
        "passenger_name": reservation.user.name,
        "seat_number": reservation.seat_number,
    }