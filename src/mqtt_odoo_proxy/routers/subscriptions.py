"""Subscriptions Router"""
from fastapi import APIRouter, HTTPException

from ..models import Subscribtion
from .clients import MQTT_THREADS

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)


@router.get("/")
async def get_subscriptions() -> list[Subscribtion]:
    """Returns all subscriptions of a client

    Returns
    -------
    list[Subscribtion]
        list of subscriptions
    """
    subscriptions = []
    for thread in MQTT_THREADS.values():
        subscriptions.extend(thread.subscriptions.values())
    return subscriptions


@router.get("/{subscription_id}/status")
async def get_subscription_status(subscription_id: int) -> Subscribtion:
    """Returns the status of a subscription

    Parameters
    ----------
    subscription_id : int
        id of the subscription

    Returns
    -------
    Subscribtion
        subscription
    """
    for thread in MQTT_THREADS.values():
        subscription = thread.subscriptions.get(subscription_id)
        if subscription:
            return subscription
    raise HTTPException(status_code=404, detail="Subscription not found")


@router.post("/add")
async def add_subscription(subscription: Subscribtion):
    """Adds a MQTT Subscription to a client

    Parameters
    ----------
    subscription : Subscribtion
        subscription to add
    """
    thread = MQTT_THREADS.get(subscription.client_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Client not found")
    thread.add_subscription(subscription)


@router.post("{subscription_id}/remove")
async def remove_subscription(client_id: int, subscription_id: int):
    """Removes a MQTT Subscription from a client

    Parameters
    ----------
    client_id : int
        id of the client to remove the subscription from
    subscription_id : int
        subscription id
    """
    thread = MQTT_THREADS.get(client_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Client not found")
    try:
        thread.remove_subscription(subscription_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail="Subscription not found") from error
