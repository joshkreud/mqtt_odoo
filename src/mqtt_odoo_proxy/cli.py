"""Commandline interface for the MQTT-Odoo bridge"""

from typing import Annotated

import typer
from typer_common_functions import set_logging
from uvicorn import run

from .api import api_app


def get_cli():
    """Returns the CLI Application"""
    cli = typer.Typer()

    @cli.command()
    def start(
        verbose: Annotated[
            bool,
            typer.Option(
                "-v",
                "--verbose",
                help="Verbose Logging",
                envvar="MQTT_ODOO_PROXY_VERBOSE",
            ),
        ] = False
    ):
        """Starts the FastAPI Server"""
        set_logging(verbose)
        run(api_app, host="0.0.0.0", port=8000)

    return cli


def launch_cli():
    """Launches the CLI Application"""
    app = get_cli()
    app()
