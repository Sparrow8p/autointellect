from fastapi import APIRouter

from app.api.routes import (
    auth,
    calculations,
    cars,
    history,
    market_prices,
    parts,
    reference,
    service_records,
    users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cars.router)
api_router.include_router(reference.router)
api_router.include_router(calculations.router)
api_router.include_router(history.router)
api_router.include_router(service_records.router)
api_router.include_router(market_prices.router)
api_router.include_router(parts.router)
