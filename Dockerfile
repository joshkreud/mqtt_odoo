# Prod Container for Lorawetter python script

ARG USERNAME=ContainerUser
FROM ghcr.io/openjksoftware/python-devcontainer:3.11 as venv

# Install Depends before the package itself to benefit from docker layercaching
WORKDIR /src
# Install from this workspace. (see pip install below)
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock ./
# Install only dependencies, so they only reinstall when lock or toml where changed
RUN poetry install --all-extras --no-root --no-interaction --no-ansi --no-dev
COPY --chown=$USERNAME:$USERNAME . .
RUN poetry install --all-extras --no-interaction --no-ansi --no-dev

FROM venv as builder
RUN rm -rf dist && poetry build -f wheel

FROM python:3.11-slim-bullseye as prod
COPY --from=builder /src/dist/*.whl /tmp/app/
RUN pip install --no-cache-dir /tmp/app/*.whl

ENTRYPOINT [ "mqtt_odoo_proxy" ]
