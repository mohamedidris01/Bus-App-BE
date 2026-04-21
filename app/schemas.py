from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, RideStatus, ReservationStatus


# --- Auth ---
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.passenger

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    role: UserRole

# --- Route ---
class RouteOut(BaseModel):
    id: int
    name: str
    start_point: str
    end_point: str
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    class Config: orm_mode = True

# --- Ride ---
class RideOut(BaseModel):
    id: int
    status: RideStatus
    departure_time: datetime
    available_seats: int
    total_seats: int
    current_lat: Optional[float]
    current_lng: Optional[float]
    location_updated_at: Optional[datetime]
    route: RouteOut
    class Config: orm_mode = True

# --- Reservation ---
class ReserveRequest(BaseModel):
    ride_id: int

class ReservationOut(BaseModel):
    id: int
    seat_number: int
    confirmation_code: str
    status: ReservationStatus
    reserved_at: datetime
    confirmed_at: Optional[datetime]
    class Config: orm_mode = True

# --- Driver ---
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float

class ConfirmPassengerRequest(BaseModel):
    code: str   # 2-digit code entered by driver

class PassengerListItem(BaseModel):
    reservation_id: int
    passenger_name: str
    seat_number: int
    status: ReservationStatus
    class Config: orm_mode = True