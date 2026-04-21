from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.ReservationOut, status_code=201)
def reserve_seat(
    payload: schemas.ReserveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ride = db.query(models.Ride).filter(models.Ride.id == payload.ride_id).first()
    if not ride:
        raise HTTPException(404, "Ride not found")
    if ride.status == models.RideStatus.completed:
        raise HTTPException(400, "Ride already completed")

    if current_user.role == models.UserRole.driver:
        raise HTTPException(403, "Drivers cannot reserve seats")

    # Check for existing reservation
    existing = db.query(models.Reservation).filter(
        models.Reservation.user_id == current_user.id,
        models.Reservation.ride_id == payload.ride_id,
        models.Reservation.status != models.ReservationStatus.cancelled,
    ).first()
    if existing:
        raise HTTPException(400, "Already reserved a seat on this ride")

    # Find next available seat
    booked_seats = {
        r.seat_number for r in ride.reservations
        if r.status != models.ReservationStatus.cancelled
    }
    all_seats = set(range(1, ride.bus.total_seats + 1))
    available = sorted(all_seats - booked_seats)
    if not available:
        raise HTTPException(400, "No seats available")

    # Generate unique 2-digit code for this ride
    existing_codes = {r.confirmation_code for r in ride.reservations}
    code = models.Reservation.generate_code()
    attempts = 0
    while code in existing_codes and attempts < 90:
        code = models.Reservation.generate_code()
        attempts += 1

    reservation = models.Reservation(
        user_id=current_user.id,
        ride_id=payload.ride_id,
        seat_number=available[0],
        confirmation_code=code,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    return reservation

@router.get("/my", response_model=List[schemas.ReservationOut])
def my_reservations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Reservation).filter(
        models.Reservation.user_id == current_user.id
    ).all()

@router.delete("/{reservation_id}", status_code=204)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    res = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id,
        models.Reservation.user_id == current_user.id,
    ).first()
    if not res:
        raise HTTPException(404, "Reservation not found")
    res.status = models.ReservationStatus.cancelled
    db.commit()