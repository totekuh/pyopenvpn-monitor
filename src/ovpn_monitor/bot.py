#!/usr/bin/env python3.7

import logging
import json
from copy import copy
from functools import wraps
from threading import Thread
from time import sleep

from openvpn_status import parse_status
from telegram import ParseMode
from telegram.ext import CommandHandler, Updater
import os

from dotenv import load_dotenv

load_dotenv()

# Use os.getenv to get environment variables
OPENVPN_STATUS_LOG_FILE = os.getenv("OPENVPN_STATUS_LOG_FILE")
TOKEN = os.getenv("TOKEN")
WHITELIST = os.getenv("WHITELIST").split(',')


class OpenVPNStatusMonitor:
    """Continuously monitor the status of an OpenVPN server."""

    def __init__(self, openvpn_status_log_file):
        self.openvpn_status_log_file = openvpn_status_log_file
        self.status = self.get_stats()
        self.status_log_thread = Thread(target=self.get_stats_in_background, args=())
        self.status_log_thread.start()

    def get_stats(self):
        """Return the current OpenVPN server stats."""
        with open(self.openvpn_status_log_file, 'r') as logfile:
            return parse_status(logfile.read())

    def get_stats_in_background(self):
        """Continuously update the OpenVPN server stats in a background thread."""
        logging.info(f'Starting a new background thread to continuously track the status log file.')
        while True:
            try:
                self.status = self.get_stats()
                sleep(3)
            except Exception as e:
                logging.error(e)
                sleep(60)

    def get_connected_clients(self):
        """Return the list of currently connected clients."""
        if self.status:
            return self.status.client_list
        else:
            return []

    def get_stats_as_string(self):
        """Return the current OpenVPN server stats as a formatted string."""
        message = ''
        message += f"Status updated at {self.status.updated_at}\n"
        client_list = self.get_connected_clients()
        if client_list:
            index = 1
            for ip_addr, client in self.status.client_list.items():
                message += f'{index} - {client.common_name} is connected '
                message += f'since {client.connected_since} '
                message += f'from {ip_addr}'
                message += '\n'
                index += 1
        return message


openvpn_monitor = OpenVPNStatusMonitor(OPENVPN_STATUS_LOG_FILE)


def track_stats(openvpn_monitor, update):
    old_clients = copy(openvpn_monitor.status.client_list)
    logging.info(f'Tracking the OpenVPN server status log for connected/disconnected entries')
    update.message.reply_text(openvpn_monitor.get_stats_as_string())
    while True:
        if openvpn_monitor.status.client_list:
            new_clients = openvpn_monitor.status.client_list

            # check if someone has disconnected the server
            for ip_addr, client in old_clients.items():
                if ip_addr not in new_clients.keys():
                    message = f'{client.common_name} from {ip_addr} has disconnected the server'
                    update.message.reply_text(message)
                    logging.info(message)

            # check if we have a new connected client
            for ip_addr, client in new_clients.items():
                if ip_addr not in old_clients.keys():
                    message = f"A new connection from {ip_addr} by {client.common_name}"
                    update.message.reply_text(message)
                    logging.info(message)

            old_clients = copy(new_clients)
            sleep(3)


def whitelist_only(func):
    """A decorator that restricts access to functions to only those in the whitelist."""

    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user = update.effective_user
        logging.info(f"@{user.username} ({user.id}) is trying to access a privileged command")
        if user.username not in WHITELIST:
            logging.warning(f"Unauthorized access denied for {user.username}.")
            text = (
                "🚫 *ACCESS DENIED*\n"
                "Sorry, you are *not authorized* to use this command"
            )
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def show_help(update, context):
    """Send a message when the command /help is issued."""
    howto = (
        f"The bot contentiously parses openvpn-status.log file "
        f"and notifies you when it detects changes between checks.\n"
        f"Use /start to start monitoring the connection logs.\n"
        f"Use /stats to print current statistics from the OpenVPN server."
    )
    update.message.reply_text(howto, parse_mode=ParseMode.MARKDOWN)


@whitelist_only
def start(update, context):
    """Start tracking the OpenVPN server status."""
    logging.info(f'{update.effective_user.username} has enabled the OpenVPN monitor')
    update.message.reply_text("Starting the OpenVPN monitor. Will contentiously check the status log for changes.")
    monitor_thread = Thread(target=track_stats, args=(openvpn_monitor, update))
    monitor_thread.start()


@whitelist_only
def stats(update, context):
    """Get current statistics of the OpenVPN server."""
    logging.info(f'{update.effective_user.username} has requested current status from the OpenVPN monitor')
    stats = openvpn_monitor.get_stats_as_string()
    if stats:
        update.message.reply_text(stats)
    else:
        update.message.reply_text('No stats are available')


def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning(f"Update {update} caused error {context.error}")


def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("help", show_help))
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_error_handler(error)

    updater.start_polling()
    logging.info("BOT DEPLOYED. Ctrl+C to terminate")

    updater.idle()


if __name__ == "__main__":
    main()
