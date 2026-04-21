from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine
from app import models
from app.routers import auth, rides, reservations, driver

# Create tables (for dev; use Alembic for production)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bus App API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(rides.router, prefix="/rides", tags=["Rides"])
app.include_router(reservations.router, prefix="/reservations", tags=["Reservations"])
app.include_router(driver.router, prefix="/driver", tags=["Driver"])

@app.get("/health")
def health():
    return {"status": "ok"}