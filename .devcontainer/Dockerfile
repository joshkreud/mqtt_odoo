FROM ghcr.io/openjksoftware/python-devcontainer:3.11
ARG WORKSPACE=/mqtt_odoo
ARG USERNAME=ContainerUser
ARG POETRY_NAME=mqtt_odoo
USER root

USER ${USERNAME}
WORKDIR ${WORKSPACE}
# ------------------------------------------------------------------------------------------------------
# Install poetry project from this workspace.
# Remove whats between the ----- and replace with: RUN pip install poetry project
COPY --chown=${USERNAME}:${USERNAME} pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-ansi --no-interaction --all-extras
# The following COPYs are below poetry install for better caching
COPY --chown=$USERNAME:$USERNAME src src
# Now install poetry project for real. Way faster now, because deps are already cached.
RUN touch README.md && poetry install --no-interaction --no-ansi --all-extras
# In the Devcontainer stage we remove everything in $WORKSPACE and replace it with a Bind-Mount
# ---------------------------------------------------------------------------------------------------------

ENV PATH=$PATH:${WORKSPACE}/scripts
