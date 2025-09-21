# -*- coding: utf-8 -*-
"""
Chat Analyzer Module - Teleforge

This module provides chat analysis features. It processes recent messages
from a selected chat to generate statistics about user activity and the
distribution of different media types.
"""
from collections import Counter
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import IntPrompt
from rich.table import Table
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, User

from utils.chat_selector import select_chat

console = Console()


async def run(client: TelegramClient):
    """
    Orchestrates the activity analysis of a given chat.

    The workflow includes:
    1. Selection of a target chat.
    2. Prompting the user for the number of recent messages to analyze.
    3. Counting messages per user to identify the most active members.
    4. Tallying the types of media shared.
    5. Displaying tables with the analysis results.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold blue]Chat Activity Analyzer Module[/bold blue]"))

    target_chat = await select_chat(client, "Select the chat to analyze:")
    if not target_chat:
        return

    limit_msgs = IntPrompt.ask(
        "\n[bold]How many recent messages do you want to analyze?[/bold]", default=1000
    )
    if limit_msgs <= 0:
        console.print("[red]Invalid number.[/red]")
        return

    console.print(
        f"\n[cyan]Analyzing the last {limit_msgs} messages from '[bold]{target_chat.name}[/bold]'. This may take a moment...[/cyan]"
    )

    user_activity = Counter()
    media_activity = Counter()

    try:
        with Progress(console=console) as progress:
            task = progress.add_task("[green]Processing messages...", total=limit_msgs)

            async for message in client.iter_messages(target_chat, limit=limit_msgs):
                progress.update(task, advance=1)

                if (
                    message.sender
                    and isinstance(message.sender, User)
                    and not message.sender.bot
                ):
                    user_name = message.sender.first_name or "Unknown User"
                    user_activity[user_name] += 1

                if message.media:
                    if isinstance(message.media, MessageMediaPhoto):
                        media_activity["Photos"] += 1
                    elif isinstance(message.media, MessageMediaDocument):
                        doc_mime_type = getattr(message.media.document, "mime_type", "")
                        if doc_mime_type.startswith("video/"):
                            media_activity["Videos"] += 1
                        elif doc_mime_type.startswith("audio/"):
                            media_activity["Audio Files"] += 1
                        else:
                            media_activity["Documents/Other"] += 1
                    else:
                        media_activity["Other Media"] += 1

        # Display the table of most active users
        console.print(
            f"\n[bold]--- Most Active Users (Last {limit_msgs} Msgs) ---[/bold]"
        )
        user_table = Table(show_header=True, header_style="bold magenta")
        user_table.add_column("Rank", style="dim")
        user_table.add_column("User Name")
        user_table.add_column("Messages Sent", justify="right")

        for i, (user, count) in enumerate(user_activity.most_common(10), 1):
            user_table.add_row(f"#{i}", user, str(count))
        console.print(user_table)

        # Display the table of media types
        console.print(
            f"\n[bold]--- Media Distribution (Last {limit_msgs} Msgs) ---[/bold]"
        )
        media_table = Table(show_header=True, header_style="bold cyan")
        media_table.add_column("Media Type")
        media_table.add_column("Count", justify="right")

        for media_type, count in media_activity.items():
            media_table.add_row(media_type, str(count))
        console.print(media_table)

    except Exception as e:
        console.print(f"\n[bold red]An error occurred during analysis: {e}[/bold red]")
