#!/usr/bin/env python3.7

import logging
import json
from copy import copy
from functools import wraps
from threading import Thread
from time import sleep

from telegram import ParseMode
from telegram.ext import CommandHandler, Updater
import os

from dotenv import load_dotenv
import copy

load_dotenv()

import sys

# Use os.getenv to get environment variables
OPENVPN_STATUS_LOG_FILE = os.getenv("OPENVPN_STATUS_LOG_FILE")
TOKEN = os.getenv("TOKEN")
WHITELIST = os.getenv("WHITELIST").split(',') if os.getenv("WHITELIST") else None

# Check if environment variables are set
if not OPENVPN_STATUS_LOG_FILE:
    print("Error: OPENVPN_STATUS_LOG_FILE environment variable is not set.")
    sys.exit(1)

if not TOKEN:
    print("Error: TOKEN environment variable is not set.")
    sys.exit(1)

if not WHITELIST:
    print("Error: WHITELIST environment variable is not set.")
    sys.exit(1)

# Check if OPENVPN_STATUS_LOG_FILE exists
if not os.path.isfile(OPENVPN_STATUS_LOG_FILE):
    print(f"Error: File {OPENVPN_STATUS_LOG_FILE} does not exist.")
    sys.exit(1)
from openvpn_status_parser import OpenVPNStatusParser


class OpenVPNStatusMonitor:
    def __init__(self, status_log_file):
        self.status_log_file = status_log_file
        self.parser = OpenVPNStatusParser(status_log_file)
        self.prev_clients = self.get_clients()  # save the initial state
        self.current_clients = copy.deepcopy(self.prev_clients)  # initialize current_clients as a copy of prev_clients

    def get_clients(self):
        self.parser = OpenVPNStatusParser(self.status_log_file)
        return {client['Common Name']: client for client in self.parser.connected_clients.values()}

    def check_for_changes(self):
        self.parser = OpenVPNStatusParser(self.status_log_file)
        self.current_clients = self.get_clients()  # update current_clients
        connected = set(self.current_clients.keys()) - set(self.prev_clients.keys())
        disconnected = set(self.prev_clients.keys()) - set(self.current_clients.keys())

        # Update the previous clients dictionary
        self.prev_clients = copy.deepcopy(self.current_clients)

        # print(self.get_clients())
        # print(connected)
        # print(disconnected)

        return connected, disconnected


openvpn_monitor = OpenVPNStatusMonitor(OPENVPN_STATUS_LOG_FILE)


def boot_main_loop(openvpn_monitor: OpenVPNStatusMonitor, update):
    while True:
        connected, disconnected = openvpn_monitor.check_for_changes()

        for client in connected:
            update.message.reply_text(text=f"VPN client connected: {client}\n",
                                           # f"Details: {details}",
                                      parse_mode=ParseMode.MARKDOWN)

        for client in disconnected:
            update.message.reply_text(text=f"VPN client disconnected: {client}",
                                      parse_mode=ParseMode.MARKDOWN)

        sleep(1)  # check every 30 seconds


def track_stats(openvpn_monitor: OpenVPNStatusMonitor, update):
    logging.info(f'Tracking the OpenVPN server status log for connected/disconnected entries')

    boot_main_loop(openvpn_monitor, update)


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
