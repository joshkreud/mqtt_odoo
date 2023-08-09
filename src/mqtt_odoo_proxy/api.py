"""Main FastAPI application"""
from fastapi import FastAPI

from .routers import clients, subscriptions

api_app = FastAPI()
api_app.include_router(clients.router)
api_app.include_router(subscriptions.router)


@api_app.get("/")
async def root():
    """Root route"""
    return {"message": "Welcome to the MQTT-Odoo bridge"}
