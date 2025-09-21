# -*- coding: utf-8 -*-
"""
Member Exporter Module - Teleforge

This module handles the functionality of exporting a group's member list
to a CSV file. It allows a user to select a group, fetches all available
members, and saves their details to a CSV. It also intelligently warns the
user if the fetched member list is incomplete due to Telegram's API
privacy restrictions for non-admins in large groups.
"""
import csv
import os
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently
from rich.console import Console
from rich.panel import Panel

from utils.chat_selector import select_chat

console = Console()


def get_user_status(user) -> str:
    """Returns a formatted string for the user's status."""
    if user.status is None:
        return "Unknown"
    if isinstance(user.status, UserStatusOnline):
        return "Online"
    if isinstance(user.status, UserStatusOffline):
        return f"Last seen on {user.status.was_online.strftime('%Y-%m-%d %H:%M')}"
    if isinstance(user.status, UserStatusRecently):
        return "Seen recently"
    return "Untracked Status"


async def run(client: TelegramClient):
    """
    Orchestrates the export of group members to a CSV file.

    The workflow includes:
    1. Selection of a target group.
    2. Collection of all available members (filtering out bots and deleted accounts).
    3. Creation of a CSV file named after the group and current date.
    4. Writing member data (ID, Username, Name, Status) to the file.
    5. Displaying a final report with the path to the saved file.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold yellow]Member Exporter Module (CSV)[/bold yellow]"))

    target_group = await select_chat(
        client, "Select the GROUP to export members from:", "group"
    )
    if not target_group:
        return

    total_known_members = target_group.entity.participants_count

    with console.status(
        f"[cyan]Collecting members from group '[bold]{target_group.name}[/bold]'...[/cyan]"
    ):
        all_participants = [
            user
            async for user in client.iter_participants(target_group.entity)
            if not user.bot and not user.deleted
        ]

    fetched_count = len(all_participants)

    if fetched_count < total_known_members:
        warning_panel = Panel(
            f"[bold]Telegram returned only [yellow]{fetched_count}[/yellow] of [yellow]{total_known_members}[/yellow] known members.[/bold]\n\n"
            "This usually happens due to privacy restrictions in large groups where you are not an administrator. Only the partial list will be exported.",
            title="[bold red]WARNING: Incomplete Member List[/bold red]",
            border_style="red",
        )
        console.print(warning_panel)

    if not all_participants:
        console.print("[red]Could not find any members in this group.[/red]")
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_group_name = "".join(
        c for c in target_group.name if c.isalnum() or c in (" ", "_")
    ).rstrip()
    filename = f"Members_{sanitized_group_name}_{date_str}.csv"
    filepath = os.path.join(os.getcwd(), filename)

    console.print(
        f"\n[cyan]Exporting [bold]{len(all_participants)}[/bold] members to file: [yellow]{filename}[/yellow]"
    )

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["User ID", "Username", "First Name", "Last Name", "Status"]
            )

            for user in all_participants:
                status = get_user_status(user)
                writer.writerow(
                    [
                        user.id,
                        user.username or "",
                        user.first_name or "",
                        user.last_name or "",
                        status,
                    ]
                )

        console.print(f"\n[bold green]--- Export Complete ---[/bold green]")
        console.print(f"Data successfully saved to: [bold]{filepath}[/bold]")

    except Exception as e:
        console.print(
            f"\n[bold red]An error occurred while writing the CSV file: {e}[/bold red]"
        )
