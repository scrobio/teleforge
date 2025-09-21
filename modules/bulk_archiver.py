# -*- coding: utf-8 -*-
"""
Bulk Chat Archiver Module - Teleforge

This module provides a utility to organize a user's chat list by
archiving multiple chats at once based on a set of rules. This helps
clean up the main chat screen efficiently.
"""
import asyncio
from datetime import datetime, timedelta, timezone

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from telethon.sync import TelegramClient

console = Console()


async def run(client: TelegramClient):
    """
    Orchestrates the process of bulk-archiving chats based on user-defined rules.

    The workflow includes:
    1. Prompting the user to select an archiving rule (e.g., by mute status, inactivity).
    2. Fetching all user dialogs.
    3. Filtering the dialogs that match the selected rule.
    4. Displaying a preview of chats to be archived for user confirmation.
    5. If confirmed, iterating through the list and archiving each chat.
    6. Reporting the final result.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold orange1]Bulk Chat Archiver Module[/bold orange1]"))

    # Display rule selection menu.
    console.print("\n[bold]Select an archiving rule:[/bold]")
    console.print("[cyan]1[/cyan] - Archive all muted chats")
    console.print("[cyan]2[/cyan] - Archive chats inactive for X days")
    console.print("[cyan]3[/cyan] - Archive all channels")
    console.print("[cyan]4[/cyan] - Archive all groups")

    choice = Prompt.ask(
        "\nEnter your choice", choices=["1", "2", "3", "4"], default="1"
    )

    with console.status("[cyan]Fetching all your chats...[/cyan]"):
        all_dialogs = await client.get_dialogs()

    chats_to_archive = []
    rule_description = ""

    # Apply the selected filter rule to the dialog list.
    if choice == "1":
        rule_description = "Muted Chats"
        for dialog in all_dialogs:
            if dialog.notify_settings and dialog.notify_settings.mute_until:
                # A future mute_until date means the chat is currently muted.
                if dialog.notify_settings.mute_until > datetime.now(timezone.utc):
                    chats_to_archive.append(dialog)

    elif choice == "2":
        days = IntPrompt.ask(
            "[bold]Archive chats with no new messages in the last (days)?[/bold]",
            default=30,
        )
        rule_description = f"Chats inactive for {days} days"
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        for dialog in all_dialogs:
            if dialog.message and dialog.message.date < cutoff_date:
                chats_to_archive.append(dialog)

    elif choice == "3":
        rule_description = "All Channels"
        for dialog in all_dialogs:
            if dialog.is_channel and not dialog.is_group:
                chats_to_archive.append(dialog)

    elif choice == "4":
        rule_description = "All Groups"
        for dialog in all_dialogs:
            if dialog.is_group:
                chats_to_archive.append(dialog)

    if not chats_to_archive:
        console.print(
            f"\n[green]✓ No chats found matching the rule: '{rule_description}'.[/green]"
        )
        return

    # Critical confirmation step: Show a preview before archiving.
    console.print(
        f"\n[bold yellow]The following {len(chats_to_archive)} chats match your rule and will be archived:[/bold yellow]"
    )
    preview_table = Table(title=f"Preview of Chats to Archive ({rule_description})")
    preview_table.add_column("Chat Name")
    preview_table.add_column("Last Message Date")

    for dialog in chats_to_archive[:10]:
        last_msg_date = (
            dialog.message.date.strftime("%Y-%m-%d") if dialog.message else "N/A"
        )
        preview_table.add_row(dialog.name, last_msg_date)
    console.print(preview_table)
    if len(chats_to_archive) > 10:
        console.print(f"[dim]...and {len(chats_to_archive) - 10} more.[/dim]")

    if (
        Prompt.ask(
            "\n[bold red]Are you sure you want to archive all these chats?[/bold red]",
            choices=["y", "n"],
            default="n",
        )
        == "y"
    ):
        with console.status(
            "[bold orange1]Archiving chats...[/bold orange1]"
        ) as status:
            for i, dialog in enumerate(chats_to_archive):
                status.update(
                    f"Archiving '{dialog.name}' ({i+1}/{len(chats_to_archive)})"
                )
                await dialog.archive()
                await asyncio.sleep(0.1)

        console.print(
            f"\n[green]Successfully archived {len(chats_to_archive)} chats.[/green]"
        )
    else:
        console.print("\n[yellow]Operation canceled.[/yellow]")
