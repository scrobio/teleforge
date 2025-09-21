# -*- coding: utf-8 -*-
"""
Contact Manager Module - Teleforge

This module is a utility for managing a user's Telegram contacts.
It helps clean up the contact list by identifying and offering to bulk-delete
two types of contacts: accounts that have been deleted, and accounts that
have been inactive for a user-defined period.
"""
from datetime import datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table
from telethon.sync import TelegramClient
from telethon.tl.types import UserStatusOffline

console = Console()


async def run(client: TelegramClient):
    """
    Orchestrates the process of finding and deleting inactive or deleted contacts.

    The workflow includes:
    1. Fetching all contacts using `client.get_contacts()`.
    2. Prompting the user to define an inactivity period (in months).
    3. Iterating through contacts, sorting them into "deleted" and "inactive" lists.
    4. Displaying the findings in clear tables for user review.
    5. Asking for final, explicit confirmation before deleting.
    6. If confirmed, performing the bulk deletion and reporting the status.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold green]Contact Manager Module[/bold green]"))

    with console.status("[cyan]Fetching your contacts...[/cyan]"):
        contacts = await client.get_contacts()

    if not contacts:
        console.print("[yellow]You do not have any contacts in your list.[/yellow]")
        return

    months = IntPrompt.ask(
        "\n[bold]Consider contacts inactive if last seen more than how many months ago?[/bold]",
        default=6,
    )
    cutoff_date = datetime.now() - timedelta(days=months * 30)

    deleted_contacts = []
    inactive_contacts = []

    for user in contacts:
        if user.deleted:
            deleted_contacts.append(user)
        elif isinstance(user.status, UserStatusOffline):
            # Convert timezone-aware datetime from Telethon to naive for comparison.
            if user.status.was_online.replace(tzinfo=None) < cutoff_date:
                inactive_contacts.append(user)

    if not deleted_contacts and not inactive_contacts:
        console.print(
            f"\n[green]✓ No deleted or inactive contacts found within the last {months} months.[/green]"
        )
        return

    contacts_to_delete = deleted_contacts + inactive_contacts

    # Display findings to the user for review before any action.
    if deleted_contacts:
        console.print("\n[bold red]--- Found Deleted Accounts ---[/bold red]")
        table = Table()
        table.add_column("User ID")
        table.add_column("Name")
        for user in deleted_contacts:
            table.add_row(str(user.id), user.first_name or "N/A")
        console.print(table)

    if inactive_contacts:
        console.print(
            f"\n[bold yellow]--- Found Inactive Contacts (Last seen > {months} months ago) ---[/bold yellow]"
        )
        table = Table()
        table.add_column("User ID")
        table.add_column("Name")
        table.add_column("Last Seen")
        for user in inactive_contacts:
            last_seen_str = user.status.was_online.strftime("%Y-%m-%d")
            table.add_row(str(user.id), user.first_name, last_seen_str)
        console.print(table)

    # Critical confirmation step before deleting data.
    console.print(
        f"\n[bold]Total contacts to be removed: {len(contacts_to_delete)}[/bold]"
    )
    if (
        Prompt.ask(
            "[bold red]Are you sure you want to delete these contacts?[/bold red]",
            choices=["y", "n"],
            default="n",
        )
        == "y"
    ):
        with console.status("[bold red]Deleting contacts...[/bold red]"):
            result = await client.delete_contacts(contacts_to_delete)
        if result:
            console.print(
                f"\n[green]Successfully deleted {len(contacts_to_delete)} contacts.[/green]"
            )
        else:
            console.print("\n[red]Failed to delete contacts.[/red]")
    else:
        console.print("\n[yellow]Operation canceled.[/yellow]")
