"""API Routes regarding MQTT Clients"""
from logging import getLogger

from fastapi import APIRouter, HTTPException

from ..models import MQTTClientArgs, MQTTThreadStatus
from ..mqtt_thread import MQTTThread

LOGGER = getLogger(__name__)

MQTT_THREADS: dict[int, MQTTThread] = {}

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
)


@router.get("/")
async def get_clients() -> list[MQTTClientArgs]:
    """List all currently running MQTT Clients

    Returns
    -------
    list[MQTTClientArgs]
        list of MQTT Clients
    """
    return [thread.client_args.model_dump(exclude=["username", "password"]) for thread in MQTT_THREADS.values()]


@router.post("/add")
async def add_client(client: MQTTClientArgs) -> MQTTThreadStatus:
    """Adds a new MQTT Client thread

    Parameters
    ----------
    client : MQTTClientArgs
        client description

    Returns
    -------
    MqttThreadStatus
        status
    """
    thread = MQTTThread(client)
    MQTT_THREADS[client.odoo_id] = thread
    thread.start()
    return MQTTThreadStatus(
        thread_id=client.odoo_id,
        thread_running=thread.is_alive(),
    )


@router.post("/{client_id}/stop")
async def stop_client(client_id: int) -> MQTTThreadStatus:
    """Stops a MQTT Client thread

    Parameters
    ----------
    client_id : int
        id of the client to stop

    Returns
    -------
    MqttThreadStatus
        status
    """
    LOGGER.info("Stopping MQTT Client %s", client_id)
    thread = MQTT_THREADS.get(client_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Client not found")
    thread.stop()
    thread.join()
    del MQTT_THREADS[client_id]
    return MQTTThreadStatus(
        thread_id=client_id,
        thread_running=False,
    )


@router.get("/{client_id}/status")
async def get_client_status(client_id: int) -> MQTTThreadStatus:
    """Return Status of a MQTT Client thread

    Parameters
    ----------
    client_id : int
        client id

    Returns
    -------
    MqttThreadStatus
        status of the thread

    Raises
    ------
    HTTPException
        if thread is not found
    """
    thread = MQTT_THREADS.get(client_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Client not found")
    return MQTTThreadStatus(
        thread_id=client_id,
        thread_running=thread.is_alive(),
        client_connected=thread.connected,
    )
