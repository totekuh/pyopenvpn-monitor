#!/usr/bin/env python3.7

import logging
from copy import copy
from functools import wraps
from threading import Thread
from time import sleep

from openvpn_status import parse_status
from telegram import ParseMode
from telegram.ext import CommandHandler, Updater

from config import OPENVPN_STATUS_LOG_FILE, TOKEN, WHITELIST


class OpenVPNStatusMonitor:
    def __init__(self, openvpn_status_log_file):
        self.openvpn_status_log_file = openvpn_status_log_file
        self.status = self.get_stats()
        self.status_log_thread = \
            Thread(target=self.get_stats_in_background, args=())
        self.status_log_thread.start()

    def get_stats(self):
        with open(self.openvpn_status_log_file, 'r') as logfile:
            return parse_status(logfile.read())

    def get_stats_in_background(self):
        logging.info(f'Starting a new background thread to continuously track the status log file.')
        while True:
            try:
                self.status = self.get_stats()
                sleep(3)
            except Exception as e:
                logging.error(e)
                exit(1)

    def get_connected_clients(self):
        if self.status:
            return self.status.client_list
        else:
            return []

    def track_stats(self):
        old_clients = copy(self.status.client_list)
        logging.info(f'Tracking the OpenVPN server status log for connected/disconnected entries')
        self.print_stats()
        while True:
            if self.status.client_list:
                new_clients = self.status.client_list

                # check if someone has disconnected the server
                for ip_addr, client in old_clients.items():
                    if ip_addr not in new_clients.keys():
                        logging.info(f'{client.common_name} from {ip_addr} has disconnected the server')

                # check if we have a new connected client
                for ip_addr, client in new_clients.items():
                    if ip_addr not in old_clients.keys():
                        logging.info(f"A new connection from {ip_addr} by {client.common_name}")

                old_clients = copy(new_clients)
                sleep(3)

    def print_stats(self):
        logging.info(f"Status updated at {self.status.updated_at}")
        client_list = self.get_connected_clients()
        if client_list:
            index = 1
            for ip_addr, client in self.status.client_list.items():
                logging.info(f'{index} - {client.common_name} is connected '
                             f'since {client.connected_since} '
                             f'from {ip_addr}')
                index += 1


def whitelist_only(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user = update.effective_user
        logging.info(
                    f"@{user.username} ({user.id}) is trying to access a privileged command"
        )
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
        f"Use /watch to start monitoring the connection logs.\n"
        f"Use /stats to print current statistics from the OpenVPN server."
    )
    update.message.reply_text(howto, parse_mode=ParseMode.MARKDOWN)


# Start tracking the OpenVPN server status.
@whitelist_only
def start(update, context):
    """Send a message when the command /start is issued."""
    logging.info(f'{update.effective_user.username} has enabled the OpenVPN monitor')
    update.message.reply_text(
                "Starting the OpenVPN monitor. Will contentiously check the status log for changes."
    )
    openvpn_monitor = OpenVPNStatusMonitor(OPENVPN_STATUS_LOG_FILE)
    monitor_thread = Thread(target=openvpn_monitor.track_stats, args=())


# Get current statistics of the OpenVPN server.
# This includes remote client addresses and their aliases.
@whitelist_only
def stats(update, context):
    logging.info(f'{update.effective_user.username} has requested current status from the OpenVPN monitor')


"""
    ERROR HANDLING
"""


# set an errors' interceptor
def error(update, context):
    """Log Errors caused by Updates."""
    logging.warning(f"Update {update} caused error {context.error}")


def main():
    logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                level=logging.INFO,
                filename="cook.log",
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
