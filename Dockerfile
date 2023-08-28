# Prod Container for Lorawetter python script

ARG USERNAME=ContainerUser
FROM ghcr.io/openjksoftware/python-devcontainer:3.11

# Install Depends before the package itself to benefit from docker layercaching
WORKDIR /src
# Install from this workspace. (see pip install below)
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock ./
# Install only dependencies, so they only reinstall when lock or toml where changed
RUN poetry install --all-extras --no-root --no-interaction --no-ansi --no-dev
COPY --chown=$USERNAME:$USERNAME . .
RUN sudo rm .env || true && poetry install --all-extras --no-interaction --no-ansi --no-dev

ENTRYPOINT [ "mqtt_odoo_proxy" ]
