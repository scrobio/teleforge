# -*- coding: utf-8 -*-
"""
Service Message Cleaner Module - Teleforge

This module provides a utility for group administrators to clean up their
chats by removing service messages. These messages, such as user join/leave
notifications, can clutter a chat over time. This tool automates the
process of finding and deleting them in bulk.
"""
import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Prompt
from telethon.sync import TelegramClient

from utils.chat_selector import select_chat

console = Console()


async def run(client: TelegramClient):
    """
    Orchestrates the process of finding and deleting service messages from a group.

    The workflow includes:
    1. Selection of a target group.
    2. A critical confirmation prompt, as deletion is irreversible.
    3. Iterating through the entire message history to find service messages.
    4. Collecting message IDs into batches.
    5. Deleting messages in batches of 100 for API efficiency.
    6. Displaying a final report of the total messages deleted.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(
        Panel(
            "[bold bright_magenta]Service Message Cleaner Module[/bold bright_magenta]"
        )
    )
    console.print(
        "[dim]This tool will delete messages like 'User joined', 'User left', 'Group photo changed', etc.[/dim]"
    )

    target_chat = await select_chat(
        client, "Select the GROUP to clean service messages from:", "group"
    )
    if not target_chat:
        return

    # A critical confirmation step is required before any destructive action.
    warning = Panel(
        "[bold]This action is PERMANENT and IRREVERSIBLE.[/bold]\n\n"
        "It will scan the entire chat history and delete ALL service messages found. "
        "This can take a long time in large groups.",
        title="[bold red]!! WARNING !![/bold red]",
        border_style="red",
    )
    console.print(warning)
    if (
        Prompt.ask(
            "[bold]Are you absolutely sure you want to proceed?[/bold]",
            choices=["y", "n"],
            default="n",
        )
        == "n"
    ):
        console.print("[yellow]Operation canceled.[/yellow]")
        return

    deleted_count = 0
    ids_to_delete = []

    try:
        total_messages_count = (await client.get_messages(target_chat, limit=0)).total

        with Progress(console=console) as progress:
            task = progress.add_task(
                "[green]Scanning messages...", total=total_messages_count
            )

            async for message in client.iter_messages(target_chat):
                progress.update(task, advance=1)

                # The `message.service` attribute is True only for system notifications.
                if message.service:
                    ids_to_delete.append(message.id)

                    # Delete in batches of 100 for maximum API efficiency.
                    if len(ids_to_delete) == 100:
                        progress.update(
                            task,
                            description=f"[magenta]Deleting a batch of {len(ids_to_delete)} messages...[/magenta]",
                        )
                        await client.delete_messages(target_chat, ids_to_delete)
                        deleted_count += len(ids_to_delete)
                        ids_to_delete = []
                        await asyncio.sleep(1)  # Brief pause to be nice to the API

            # Delete any remaining messages after the loop finishes.
            if ids_to_delete:
                progress.update(
                    task,
                    description=f"[magenta]Deleting the final batch of {len(ids_to_delete)} messages...[/magenta]",
                )
                await client.delete_messages(target_chat, ids_to_delete)
                deleted_count += len(ids_to_delete)

        summary = Panel(
            f"[bold]Cleaning complete![/bold]\nSuccessfully deleted [green]{deleted_count}[/green] service messages from the chat.",
            title="[bold green]Process Finished[/bold green]",
        )
        console.print(summary)

    except Exception as e:
        console.print(
            f"\n[bold red]An error occurred during the cleaning process: {e}[/bold red]"
        )
        console.print(
            "[yellow]Note: You must be an administrator in the group with permission to delete messages.[/yellow]"
        )
