# Odoo MQTT Adapter

Fastapi service to Listen for MQTT Events and push Messages to Odoo
Exposes Rest API to change Listening MQTT Servers and so on.


start using `make dev`
swagger docs at `localhost:8000/docs`


## Devumgebung

Damit es sich einfacher starten läst, wird hier einfach mit admin zugängen gearbeitet.
Das sollte in Prod anders laufen.

Das Pythonscript wird per [Poetry](https://python-poetry.org/docs/) und nicht per Pip verwalet, das vereinfacht einige Dinge.
Allerdings ist das im Devcontainer auch schon vorinstalliert.

## Vorbereitung

Zuerst muss folgendes installiert sein:
- [docker](https://www.docker.com/)
- [docker compose](https://docs.docker.com/compose/install/)
- Traefik (nicht wichtig zur ausführung, macht nur das DNS einfacher) [Beispiel](https://github.com/joshkreud/traefik_devproxy)

## Devcontainer

Diesen Order kann man als [Devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) starten.

1. Öffnen des Ordners in Vscode (Nicht den darüber, sondern diesen hier)
2. Strg+Shift+P --> Reopen in Container (Oder die Notification unten links anklicken, wenn sie kommt)
3. Nach einiger wartezeit sollte man dann in einer sauberen python umgebung mit `weather_mqtt` als CLI command landen.
4. postgres Ist unter dem host `db` erreichbar.
5. Es sollte dann auch ein Grafana unter https://lorawetter.docker.localhost/ laufen, welches auch schon mit der postgres verbuden ist.
