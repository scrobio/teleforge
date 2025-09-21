# -*- coding: utf-8 -*-
"""
Advanced Downloader Module - Teleforge

This module enhances the original downloader with advanced filtering
capabilities. It allows the user to select a chat and then apply filters
to download only specific media types (photos, videos, etc.) and/or media
sent by a specific user within that chat.
"""
import os

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn
from rich.prompt import Prompt
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto, User

from utils.chat_selector import select_chat

console = Console()


def check_media_type(message, media_filter: str) -> bool:
    """
    Helper function to check if a message's media matches the selected filter.

    Args:
        message: The Telethon message object.
        media_filter (str): The filter criteria ('all', 'photos', 'videos', etc.).

    Returns:
        bool: True if the media type matches the filter, False otherwise.
    """
    if media_filter == "all":
        return True
    if media_filter == "photos":
        return isinstance(message.media, MessageMediaPhoto)

    if isinstance(message.media, MessageMediaDocument):
        doc_mime_type = getattr(message.media.document, "mime_type", "")
        if media_filter == "videos":
            return doc_mime_type.startswith("video/")
        if media_filter == "audio":
            return doc_mime_type.startswith("audio/")
        if media_filter == "documents":
            return not doc_mime_type.startswith(
                "video/"
            ) and not doc_mime_type.startswith("audio/")
    return False


async def run(client: TelegramClient):
    """
    Orchestrates the media download process with advanced filtering.

    The workflow includes:
    1. Selection of a target chat.
    2. Prompting the user to select media type and user filters.
    3. Iterating through all messages while applying the selected filters.
    4. Downloading only the messages that match the criteria.
    5. Displaying a final report.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold cyan]Advanced Media Downloader Module[/bold cyan]"))

    target_chat = await select_chat(client, "Select the chat to download media from:")
    if not target_chat:
        return

    console.print("\n[bold]Select a media type to download:[/bold]")
    console.print("[cyan]1[/cyan] - All Media Types")
    console.print("[cyan]2[/cyan] - Photos Only")
    console.print("[cyan]3[/cyan] - Videos Only")
    console.print("[cyan]4[/cyan] - Documents (PDF, ZIP, etc.)")
    console.print("[cyan]5[/cyan] - Audio Files")

    media_choice = Prompt.ask(
        "Enter your choice", choices=["1", "2", "3", "4", "5"], default="1"
    )
    media_filter_map = {
        "1": "all",
        "2": "photos",
        "3": "videos",
        "4": "documents",
        "5": "audio",
    }
    media_filter = media_filter_map[media_choice]

    user_filter_id = None
    if (
        Prompt.ask(
            "\n[bold]Do you want to filter by a specific user?[/bold]",
            choices=["y", "n"],
            default="n",
        )
        == "y"
    ):
        with console.status("[cyan]Fetching users in chat...[/cyan]"):
            participants = [
                user
                async for user in client.iter_participants(target_chat.entity)
                if isinstance(user, User)
            ]

        console.print("\n[bold green]Select a user to filter by:[/bold green]")
        for i, user in enumerate(participants):
            console.print(f"  [{i}] - {user.first_name}")

        user_choice = Prompt.ask("Enter the user's number")
        try:
            user_filter_id = participants[int(user_choice)].id
        except (ValueError, IndexError):
            console.print(
                "[red]Invalid user selection. Proceeding without user filter.[/red]"
            )

    main_download_folder = "downloads"
    sanitized_chat_name = "".join(
        c for c in target_chat.name if c.isalnum() or c in (" ", "_")
    ).rstrip()
    download_path = os.path.join(os.getcwd(), main_download_folder, sanitized_chat_name)
    os.makedirs(download_path, exist_ok=True)

    console.print(
        f"\n[cyan]Preparing to download from '[bold]{target_chat.name}[/bold]' with active filters.[/cyan]"
    )
    console.print(f"Files will be saved in: [yellow]{download_path}[/yellow]")

    try:
        total_messages_count = (await client.get_messages(target_chat, limit=0)).total
        if total_messages_count == 0:
            console.print(
                "[yellow]The chat has no messages. Nothing to download.[/yellow]"
            )
            return

        downloaded_files = 0
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            TextColumn("({task.completed}/{task.total})"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[green]Scanning messages...", total=total_messages_count
            )

            async for message in client.iter_messages(target_chat):
                progress.update(task, advance=1)

                # Apply all selected filters before deciding to download.
                should_download = message.media and not getattr(
                    message, "service", False
                )
                if should_download and user_filter_id:
                    should_download = message.sender_id == user_filter_id
                if should_download:
                    should_download = check_media_type(message, media_filter)

                if should_download:
                    try:
                        file_path = await message.download_media(file=download_path)
                        if file_path:
                            downloaded_files += 1
                            progress.update(
                                task,
                                description=f"[green]Downloading... ({downloaded_files} saved)[/green]",
                            )
                    except Exception as e:
                        console.print(f"[red]\nError downloading a file: {e}[/red]")

        console.print(f"\n\n[bold green]--- Process Complete ---[/bold green]")
        console.print(f"Total media files downloaded: [bold]{downloaded_files}[/bold]")
    except Exception as e:
        console.print(f"\n[bold red]An unexpected error occurred: {e}[/bold red]")
