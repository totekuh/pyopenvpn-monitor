FROM python:3.7.7-slim-stretch
COPY ./requirements.txt /ovpn-bot/requirements.txt
RUN pip3 install -r /ovpn-bot/requirements.txt

COPY config.py /ovpn-bot/
COPY ovpn-bot.py /ovpn-bot/

ENTRYPOINT ['python3.7', '/ovpn-bot/ovpn-bot.py']
