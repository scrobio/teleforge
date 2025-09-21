# -*- coding: utf-8 -*-
"""
Chat Selector Utility - Teleforge

This module provides a reusable function to display a list of a user's
Telegram chats (groups and channels), allowing for interactive selection.
It abstracts away the logic of fetching, filtering, and prompting for
user input.
"""
from telethon.sync import TelegramClient
from telethon.tl.types import Dialog
from rich.console import Console
from rich.prompt import IntPrompt

console = Console()


async def select_chat(
    client: TelegramClient, title_prompt: str, chat_type: str = "any"
) -> Dialog | None:
    """
    Fetches, filters, and displays the user's chats for interactive selection.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
        title_prompt (str): The prompt/title to display to the user above the list.
        chat_type (str, optional): The type of chat to filter for.
            Options: 'group', 'channel', 'any'. Defaults to 'any'.

    Returns:
        Dialog | None: The Telethon `Dialog` object corresponding to the
        user's choice, or `None` if the operation is canceled or no chats are found.
    """
    console.print("[yellow]Loading chat list...[/yellow]")
    dialogs = await client.get_dialogs()

    chats = []
    for d in dialogs:
        # The filtering logic distinguishes groups from broadcast channels.
        # Telegram considers "megagroups" as a type of channel, so we need to
        # explicitly exclude them if we only want broadcast channels.
        is_group = d.is_group
        is_channel = d.is_channel and not getattr(d.entity, "megagroup", False)

        if chat_type == "group" and is_group:
            chats.append(d)
        elif chat_type == "channel" and is_channel:
            chats.append(d)
        elif chat_type == "any":
            chats.append(d)

    if not chats:
        console.print(
            f"[bold red]No chats of type '{chat_type}' were found.[/bold red]"
        )
        return None

    console.print(f"\n[bold green]{title_prompt}[/bold green]")
    for i, chat in enumerate(chats):
        console.print(f"  [{i}] - {chat.name}")

    while True:
        # The default value 'len(chats)' acts as an implicit "cancel" option,
        # as it is outside the list's valid index range (0 to len-1).
        choice = IntPrompt.ask(
            f"\n[bold]Enter the chat NUMBER (or press Enter to cancel)[/bold]",
            default=len(chats),
        )

        if 0 <= choice < len(chats):
            return chats[choice]
        elif choice == len(chats):
            console.print("[yellow]Selection canceled.[/yellow]")
            return None

        console.print("[red]Invalid number. Please try again.[/red]")
