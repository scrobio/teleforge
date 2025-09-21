# -*- coding: utf-8 -*-
"""
Global Search Module - Teleforge

This module provides a "global search" feature, allowing the user to
search for a keyword across all their Telegram chats. It compiles the
results into a single, easy-to-read text file, creating an exportable
and permanent search log.
"""
import os
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, User

console = Console()


async def run(client: TelegramClient):
    """
    Orchestrates a global search across all chats for a keyword.

    The workflow includes:
    1. Prompting the user for a search term.
    2. Creating a uniquely named text file for the results.
    3. Using `client.iter_messages(None, ...)` to perform the global search.
    4. For each found message, extracting key details (chat, sender, date, link, text).
    5. Writing these details to the text file.
    6. Displaying a final summary panel with the result count and report path.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold blue]Global Search Module[/bold blue]"))

    keyword = Prompt.ask("\n[bold]Enter the keyword or phrase to search for[/bold]")
    if not keyword:
        console.print("[red]Search term cannot be empty.[/red]")
        return

    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"Global_Search_{keyword.replace(' ', '_')}_{date_str}.txt"
    filepath = os.path.join(os.getcwd(), filename)

    found_count = 0
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"--- Search Results for '{keyword}' ---\n\n")

            status_message = (
                "[cyan]Searching across all chats... This can take a long time.[/cyan]"
            )
            with console.status(status_message):
                # Using entity=None performs a global search across all dialogs.
                async for message in client.iter_messages(None, search=keyword):
                    # Safely get the chat title.
                    chat_title = "Unknown Chat"
                    if hasattr(message.chat, "title"):
                        chat_title = message.chat.title

                    # Determine the sender's name, handling both Users and Channels.
                    sender_name = "N/A"
                    if isinstance(message.sender, User):
                        sender_name = message.sender.first_name
                    elif isinstance(message.sender, Channel):
                        sender_name = message.sender.title

                    # Create a clickable link to the message.
                    # Note: These links work best for public/private channels and supergroups.
                    message_link = f"https://t.me/c/{message.chat_id}/{message.id}"

                    f.write("----------------------------------------\n")
                    f.write(f"Chat: {chat_title} (ID: {message.chat_id})\n")
                    f.write(f"From: {sender_name}\n")
                    f.write(f"Date: {message.date.strftime('%Y-%m-%d %H:%M')}\n")
                    f.write(f"Link: {message_link}\n")
                    f.write(f"Text: {message.text}\n\n")

                    found_count += 1

        summary_panel = Panel(
            f"[bold]Search complete![/bold]\nFound [green]{found_count}[/green] messages.\n\nResults saved to:\n[yellow]{filepath}[/yellow]",
            title="[bold green]Search Finished[/bold green]",
        )
        console.print(summary_panel)

    except Exception as e:
        console.print(
            f"\n[bold red]An error occurred during the search: {e}[/bold red]"
        )
