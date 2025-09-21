# -*- coding: utf-8 -*-
"""
Messaging Module - Teleforge

This module contains the functionality to send direct messages (DMs) to
members of a selected group.

WARNING: The functions in this module perform actions that can be easily
interpreted as spam by Telegram's systems. Improper use can result in
severe limitations or a permanent ban of the account. Use with extreme
caution and responsibility.
"""
import asyncio
import random
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt

from utils.chat_selector import select_chat

console = Console()


async def run(client: TelegramClient):
    """
    Orchestrates the process of sending messages to group members.

    The workflow includes:
    1. Displaying a security warning and asking for confirmation.
    2. Selection of a target group.
    3. Collection of all available members (filtering bots and deleted accounts).
    4. Prompting for the message content and the number of recipients.
    5. Sending messages to a random sample of members, with a significant,
       random safety delay between each send.
    6. Handling common errors and providing a final report.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(Panel("[bold magenta]Bulk Messenger Module[/bold magenta]"))

    warning = Panel(
        "[bold]This feature is powerful and risky. Sending bulk DMs can lead to your account being limited or permanently banned by Telegram. Use with extreme caution and at your own risk. A long, random delay will be applied between sends.[/bold]",
        title="[bold red]SECURITY WARNING[/bold red]",
        border_style="red",
    )
    console.print(warning)

    if (
        Prompt.ask(
            "[bold]Do you understand the risks and wish to continue?[/bold]",
            choices=["y", "n"],
            default="n",
        )
        == "n"
    ):
        console.print("[yellow]Operation canceled.[/yellow]")
        return

    target_group = await select_chat(
        client, "Select the GROUP to send messages to:", "group"
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
    console.print(
        f"[green]Total members found: [bold]{fetched_count}[/bold] (out of {total_known_members} known)[/green]"
    )

    if fetched_count < total_known_members:
        console.print(
            Panel(
                "[bold yellow]WARNING:[/bold yellow] Telegram did not return the full member list (likely because you are not an admin). Messages will only be sent to a subset of the found members.",
                border_style="yellow",
            )
        )

    if not all_participants:
        console.print("[red]No members found to send messages to.[/red]")
        return

    console.print(
        "\n[bold]Enter the message you want to send. To create a new line, use '\\n'.[/bold]"
    )
    message_to_send = Prompt.ask("> ").replace("\\n", "\n")

    amount = IntPrompt.ask(
        f"\n[bold]How many (random) members do you want to message? (max: {fetched_count})[/bold]",
        default=1,
    )
    if not (0 < amount <= fetched_count):
        console.print("[red]Invalid value.[/red]")
        return

    members_to_message = random.sample(all_participants, amount)

    console.print(
        f"\n[cyan]Starting to send messages to [bold]{len(members_to_message)}[/bold] member(s).[/cyan]"
    )
    success, failure = 0, 0

    for i, member in enumerate(members_to_message):
        try:
            console.print(
                f"\n({i+1}/{amount}) Sending to: [bold]{member.first_name}[/bold] (ID: {member.id})"
            )
            await client.send_message(member.id, message_to_send)
            console.print("  [green] -> Message sent successfully.[/green]")
            success += 1
        except UserPrivacyRestrictedError:
            console.print(
                "  [yellow] -> Failed: User's privacy settings do not allow DMs.[/yellow]"
            )
            failure += 1
        except PeerFloodError:
            console.print(
                "[bold red]!!! PEER FLOOD ERROR DETECTED BY TELEGRAM !!![/bold red]"
            )
            console.print(
                "[bold yellow]This means your account has been limited. STOP all automation for 24-48h and 'warm up' the account with manual usage.[/bold yellow]"
            )
            failure += 1
            break
        except Exception as e:
            console.print(f"  [red] -> Failed to send: {e}[/red]")
            failure += 1

        if i < amount - 1:
            delay = random.randint(45, 90)
            with console.status(
                f"[dim]Waiting {delay}s to avoid flood...[/dim]", spinner="dots"
            ):
                await asyncio.sleep(delay)

    summary = Panel(
        f"[bold]Successes:[/bold] [green]{success}[/green]\n[bold]Failures:[/bold] [red]{failure}[/red]",
        title="[bold]Send Complete[/bold]",
    )
    console.print(summary)
