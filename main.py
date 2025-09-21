# -*- coding: utf-8 -*-
"""
Main Entry Point - Teleforge

This script serves as the central orchestrator for the Teleforge application.
It is responsible for initializing the user interface, managing the main menu,
and delegating execution to the functional modules based on user choice.
"""
import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import pyfiglet

# Import the main run functions from their respective packages
from core.client import get_client
from modules.downloader import run as run_downloader
from modules.messaging import run as run_messaging
from modules.member_exporter import run as run_member_exporter
from modules.chat_analyzer import run as run_chat_analyzer
from modules.contact_manager import run as run_contact_manager
from modules.global_search import run as run_global_search
from modules.bulk_archiver import run as run_bulk_archiver
from modules.chat_archiver import run as run_chat_archiver
from modules.watermarker import run as run_watermarker

console = Console()


def display_banner():
    """Displays the application's startup banner using ASCII art."""
    banner = pyfiglet.figlet_format("Teleforge", font="slant")
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    console.print(" " * 22 + "[dim]Your automation toolkit for Telegram[/dim]\n")


def display_menu():
    """Renders and displays the main options menu panel."""
    # Using a multi-line string is cleaner for larger text blocks.
    menu_text = """
[bold]Choose an option:[/bold]

[cyan]1[/cyan] - [bold]Downloader:[/bold] Download media with advanced filters.
[magenta]2[/magenta] - [bold]Messenger:[/bold] Send DMs to group members.
[yellow]3[/yellow] - [bold]Member Exporter:[/bold] Save a member list to a CSV file.
[blue]4[/blue] - [bold]Chat Analyzer:[/bold] View chat activity statistics.
[green]5[/green] - [bold]Contact Manager:[/bold] Find and delete inactive/deleted contacts.
[purple]6[/purple] - [bold]Global Search:[/bold] Search for a keyword across all your chats.
[orange1]7[/orange1] - [bold]Bulk Archiver:[/bold] Archive multiple chats based on rules.
[green_yellow]8[/green_yellow] - [bold]Chat Archiver:[/bold] Export a chat's text history to a file.
[medium_purple]9[/medium_purple] - [bold]Watermarker:[/bold] Apply a watermark to a folder of images.

[red]0[/red] - [bold]Exit[/bold]
    """
    console.print(Panel(menu_text, title="Main Menu", border_style="green"))


async def main():
    """
    Orchestrates the main execution of the application.

    This function manages the application's lifecycle:
    1. Establishes the connection to the Telegram client.
    2. Enters the main menu loop.
    3. Calls the modules selected by the user.
    4. Ensures a safe disconnection upon exit.
    """
    client = await get_client()
    if not client:
        # If the connection fails, the application cannot proceed.
        return

    # The 'async with' block ensures the client disconnects safely upon exit.
    async with client:
        menu_options = {
            "1": run_downloader,
            "2": run_messaging,
            "3": run_member_exporter,
            "4": run_chat_analyzer,
            "5": run_contact_manager,
            "6": run_global_search,
            "7": run_bulk_archiver,
            "8": run_chat_archiver,
            "9": run_watermarker,  # NOVA LINHA
        }
        while True:
            # Clear the console screen for a cleaner interface on each menu cycle.
            os.system("cls" if os.name == "nt" else "clear")

            display_banner()
            display_menu()

            choice = Prompt.ask(
                "[bold]Enter your choice[/bold]",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                default="0",
            )

            if choice == "0":
                console.print("\n[bold yellow]Disconnecting... Goodbye![/bold yellow]")
                break

            # Get the function from the corresponding module based on user choice.
            selected_function = menu_options.get(choice)
            if selected_function:
                # Pass the connected client to the selected module.
                await selected_function(client)

            Prompt.ask("\n[dim]Press Enter to return to the menu...[/dim]")


if __name__ == "__main__":
    """
    Script entry point.
    This block is executed only when the script is run directly.
    """
    asyncio.run(main())
