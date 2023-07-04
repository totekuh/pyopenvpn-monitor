# OpenVPN Status Monitor

OpenVPN Status Monitor is a Python-based bot that monitors the status of an OpenVPN server and sends updates to a specified Telegram channel.

## Features

- Real-time monitoring of OpenVPN status log.
- Notification of new connections and disconnections.
- Whitelist access control for privileged bot commands.

## Installation

Clone the repository.

```bash
git clone https://github.com/username/openvpn-status-monitor.git
```

Navigate to the project directory.

```bash
cd openvpn-status-monitor
```

Install the Python package.

```bash
pip install .
```

## Docker Deployment

Build the Docker image.

```bash
docker-compose build
```


Start the Docker container.

```bash
docker-compose up -d
```

## Configuration

Configuration of the OpenVPN Status Monitor is done via environment variables which can be placed in a .env file. An example .env file is provided in the repository. Please make sure to replace the placeholders with your actual values.

```dotenv
# .env example
TOKEN=your_telegram_token
OPENVPN_STATUS_LOG_FILE=/path/to/openvpn/status.log
WHITELIST=whitelisted_telegram_usernames_separated_by_comma
```

Please note that the `OPENVPN_STATUS_LOG_FILE` environment variable refers to the OpenVPN status log file inside the Docker container. 
Therefore, you have to ensure that the status log file of your OpenVPN server is properly mounted into the Docker container using Docker volumes. 

The docker-compose file provided in the repository uses this environment variable to correctly mount your OpenVPN status log file.

## Usage

- `/start` command: Start monitoring the connection logs.
- `/stats` command: Print current statistics from the OpenVPN server.
- `/help` command: Show help message.

