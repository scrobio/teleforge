# -*- coding: utf-8 -*-
"""
Chat History Archiver Module - Teleforge

This module provides a flexible tool for exporting the text history of any
Telegram chat to a local file. It supports various date ranges and output
formats (TXT, JSON), making it ideal for creating backups or searchable logs.
"""
import json
import os
from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from telethon.sync import TelegramClient
from telethon.tl.types import Channel, User

from utils.chat_selector import select_chat

console = Console()


def get_date_range(choice: str) -> tuple[datetime | None, datetime | None]:
    """
    Processes a user's menu choice to generate a date range for filtering messages.

    Args:
        choice (str): The user's menu selection ('1', '2', '3', or '4').

    Returns:
        tuple[datetime | None, datetime | None]: A tuple containing timezone-aware
        start and end dates. Returns (None, None) if all messages are selected.
    """
    now = datetime.now(timezone.utc)

    if choice == "1":
        return None, None
    if choice == "2":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_date, None
    if choice == "3":
        yesterday = now - timedelta(days=1)
        start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_date, end_date
    if choice == "4":
        while True:
            try:
                start_str = Prompt.ask("[bold]Enter start date (YYYY-MM-DD)[/bold]")
                end_str = Prompt.ask("[bold]Enter end date (YYYY-MM-DD)[/bold]")
                start_date = datetime.strptime(start_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
                end_date = (
                    datetime.strptime(end_str, "%Y-%m-%d") + timedelta(days=1)
                ).replace(tzinfo=timezone.utc)
                return start_date, end_date
            except ValueError:
                console.print("[red]Invalid date format. Please use YYYY-MM-DD.[/red]")
    return None, None


async def run(client: TelegramClient):
    """
    Orchestrates the process of archiving a chat's text history to a file.

    The workflow includes:
    1. Selection of a target chat.
    2. Prompting for the export format (TXT or JSON).
    3. Prompting for the desired time period to archive.
    4. Fetching all messages within the specified date range.
    5. Writing the formatted messages to a local file.
    6. Displaying a final summary report.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(
        Panel("[bold green_yellow]Chat History Archiver Module[/bold green_yellow]")
    )

    target_chat = await select_chat(client, "Select the chat to archive:")
    if not target_chat:
        return

    console.print("\n[bold]Select an export format:[/bold]")
    console.print("[cyan]1[/cyan] - Plain Text (.txt)")
    console.print("[cyan]2[/cyan] - JSON (.json)")
    format_choice = Prompt.ask("Enter your choice", choices=["1", "2"], default="1")
    file_extension = "txt" if format_choice == "1" else "json"

    console.print("\n[bold]Select a time period to archive:[/bold]")
    console.print("[cyan]1[/cyan] - All messages")
    console.print("[cyan]2[/cyan] - Today's messages")
    console.print("[cyan]3[/cyan] - Yesterday's messages")
    console.print("[cyan]4[/cyan] - Custom date range")
    date_choice = Prompt.ask(
        "Enter your choice", choices=["1", "2", "3", "4"], default="1"
    )

    start_date, end_date = get_date_range(date_choice)

    date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_chat_name = "".join(
        c for c in target_chat.name if c.isalnum() or c in (" ", "_")
    ).rstrip()
    filename = f"Archive_{sanitized_chat_name}_{date_str}.{file_extension}"
    filepath = os.path.join(os.getcwd(), filename)

    messages_to_write = []
    found_count = 0

    try:
        status_message = f"[cyan]Fetching messages from '[bold]{target_chat.name}[/bold]'... This may take a while.[/cyan]"
        with console.status(status_message):
            # We iterate backwards from the newest message (or from end_date if specified).
            async for message in client.iter_messages(
                target_chat, offset_date=end_date, limit=None
            ):
                # Stop iterating if we've gone past the start_date.
                if start_date and message.date < start_date:
                    break

                sender_name = "N/A"
                if isinstance(message.sender, User):
                    sender_name = message.sender.first_name or "Unknown"
                elif isinstance(message.sender, Channel):
                    sender_name = message.sender.title

                text = message.text or "[Media or other non-text content]"

                messages_to_write.append(
                    {
                        "timestamp": message.date.isoformat(),
                        "sender": sender_name,
                        "text": text,
                    }
                )
                found_count += 1

        with open(filepath, "w", encoding="utf-8") as f:
            if file_extension == "json":
                json.dump(messages_to_write, f, indent=2, ensure_ascii=False)
            else:
                for msg in reversed(messages_to_write):
                    f.write(
                        f"[{datetime.fromisoformat(msg['timestamp']).strftime('%Y-%m-%d %H:%M')}] {msg['sender']}:\n"
                    )
                    f.write(f"{msg['text']}\n")
                    f.write("-" * 20 + "\n")

        summary = Panel(
            f"[bold]Archive complete![/bold]\nFound and saved [green]{found_count}[/green] messages.\n\nResults saved to:\n[yellow]{filepath}[/yellow]",
            title="[bold green]Archive Finished[/bold green]",
        )
        console.print(summary)

    except Exception as e:
        console.print(f"\n[bold red]An error occurred during archiving: {e}[/bold red]")
