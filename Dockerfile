# Dockerfile
FROM python:3.9-slim-buster

RUN pip3 install --upgrade pip

ENV APP_HOME="/app"

WORKDIR $APP_HOME

COPY setup.py "$APP_HOME/"
COPY pyproject.toml "$APP_HOME/"
COPY src/ "$APP_HOME/src/"
COPY README.md "$APP_HOME/"

COPY .env "$APP_HOME/"

RUN pip3 install .

ENTRYPOINT ["ovpn-monitor"]
