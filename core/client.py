# -*- coding: utf-8 -*-
"""
Client Manager - Teleforge

This module is central to the application, responsible for all logic
related to connecting and authenticating with the Telegram API.

It reads credentials from the configuration file, establishes the client session,
and manages the interactive login flow on the first run, ensuring that
other modules receive a ready-to-use client instance.
"""

import configparser
import os
from getpass import getpass

from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import SessionPasswordNeededError, ApiIdInvalidError
from rich.console import Console

console = Console()


def load_config(filename: str = "config.ini") -> tuple | tuple:
    """
    Reads and validates the `config.ini` configuration file.

    Args:
        filename (str, optional): The name of the configuration file.
            Defaults to "config.ini".

    Returns:
        tuple: A tuple containing (api_id, api_hash, session_name) on success.
        tuple: A tuple containing (None, None, None) on failure.
    """
    config = configparser.ConfigParser()
    if not os.path.exists(filename):
        console.print(
            f"[bold red]Error: Configuration file '{filename}' not found.[/bold red]"
        )
        return None, None, None

    config.read(filename)
    try:
        api_id = config.getint("telegram_credentials", "api_id")
        api_hash = config.get("telegram_credentials", "api_hash")
        session_name = config.get("session_settings", "session_name")
        return api_id, api_hash, session_name
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        # This block handles common errors from a malformed .ini file.
        console.print(f"[bold red]Error in configuration file: {e}[/bold red]")
        return None, None, None


async def get_client() -> TelegramClient | None:
    """
    Creates, connects, and authenticates the Telethon client.

    This function acts as a "factory" for the Telegram client. It handles
    reading credentials, the initial connection, and the interactive login
    flow (phone number, code, 2FA password) on the first run.

    Returns:
        TelegramClient | None: The fully connected and authorized client
        instance on success, or None if any error occurs.
    """
    api_id, api_hash, session_name = load_config()
    if not all((api_id, api_hash, session_name)):
        return None

    client = TelegramClient(session_name, api_id, api_hash)

    try:
        await client.connect()
        # If the session file doesn't exist or is invalid, the client won't be authorized.
        if not await client.is_user_authorized():
            console.print(
                "[yellow]First login detected. Please enter your credentials.[/yellow]"
            )
            phone = input("Enter your phone number (e.g., +14155552671): ")
            await client.send_code_request(phone)
            try:
                await client.sign_in(phone, input("Enter the code you received: "))
            except SessionPasswordNeededError:
                # Occurs if the account has Two-Factor Authentication (2FA) enabled.
                # getpass hides password input in the terminal for security.
                await client.sign_in(
                    password=getpass("Two-Factor Authentication password: ")
                )

        console.print(
            "[bold green]Telegram client connected successfully![/bold green]"
        )
        return client

    except ApiIdInvalidError:
        console.print(
            f"[bold red]Error: Invalid API ID or API Hash. Please check your 'config.ini'.[/bold red]"
        )
        return None
    except Exception as e:
        console.print(
            f"[bold red]An unexpected error occurred during connection: {e}[/bold red]"
        )
        return None
