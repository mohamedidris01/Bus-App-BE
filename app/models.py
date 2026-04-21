import random
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    ForeignKey, DateTime, Enum
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    passenger = "passenger"
    driver = "driver"


class RideStatus(str, enum.Enum):
    scheduled = "scheduled"
    active = "active"
    completed = "completed"


class ReservationStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"   # driver scanned code
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.passenger)
    created_at = Column(DateTime, default=datetime.utcnow)

    reservations = relationship("Reservation", back_populates="user")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)            # e.g. "Route A"
    start_point = Column(String, nullable=False)     # e.g. "Central Station"
    end_point = Column(String, nullable=False)       # e.g. "Airport"
    start_lat = Column(Float, nullable=False)
    start_lng = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lng = Column(Float, nullable=False)

    rides = relationship("Ride", back_populates="route")


class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, nullable=False)
    total_seats = Column(Integer, default=30)

    rides = relationship("Ride", back_populates="bus")


class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(RideStatus), default=RideStatus.scheduled)
    departure_time = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Live GPS location (updated by driver app via polling push)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    location_updated_at = Column(DateTime, nullable=True)

    bus = relationship("Bus", back_populates="rides")
    route = relationship("Route", back_populates="rides")
    driver = relationship("User")
    reservations = relationship("Reservation", back_populates="ride")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ride_id = Column(Integer, ForeignKey("rides.id"), nullable=False)
    seat_number = Column(Integer, nullable=False)
    # 2-digit confirmation code shown to passenger, used by driver
    confirmation_code = Column(String(2), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.pending)
    reserved_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="reservations")
    ride = relationship("Ride", back_populates="reservations")

    @staticmethod
    def generate_code() -> str:
        """Generate a unique 2-digit numeric code (10–99)."""
        return str(random.randint(10, 99))