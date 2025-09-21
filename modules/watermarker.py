# -*- coding: utf-8 -*-
"""
Image Watermarker Module - Teleforge

This module provides a powerful tool for content creators to apply a
watermark to a batch of images and upload them directly to a Telegram chat.
It uses the Pillow library for image manipulation and offers various options
for customization, such as position, scale, and opacity.
"""
import io
import os

from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import IntPrompt, Prompt
from telethon.sync import TelegramClient

from utils.chat_selector import select_chat

console = Console()


def apply_watermark(
    image_path: str, watermark_path: str, options: dict
) -> io.BytesIO | None:
    """
    Applies a watermark to a single image using Pillow.

    This function handles opening the images, resizing the watermark proportionally,
    adjusting its opacity, calculating its position, and compositing it onto the
    base image. The final result is returned as an in-memory bytes object to
    avoid writing temporary files to disk.

    Args:
        image_path (str): The file path to the base image.
        watermark_path (str): The file path to the watermark image.
        options (dict): A dictionary containing 'scale', 'opacity', and 'position'.

    Returns:
        io.BytesIO | None: An in-memory bytes object of the final JPEG image,
        or None if an error occurred.
    """
    try:
        with Image.open(image_path).convert("RGBA") as base_image, Image.open(
            watermark_path
        ).convert("RGBA") as watermark:

            # Resize watermark to be a percentage of the base image's width.
            ratio = watermark.height / watermark.width
            new_watermark_width = int(base_image.width * (options["scale"] / 100))
            new_watermark_height = int(new_watermark_width * ratio)
            watermark = watermark.resize(
                (new_watermark_width, new_watermark_height), Image.Resampling.LANCZOS
            )

            # Adjust opacity by modifying the alpha channel.
            if options["opacity"] < 100:
                alpha = watermark.getchannel("A")
                new_alpha = alpha.point(lambda p: p * (options["opacity"] / 100))
                watermark.putalpha(new_alpha)

            # Calculate the paste position based on user's choice.
            padding = 10
            positions = {
                "1": (
                    base_image.width - watermark.width - padding,
                    base_image.height - watermark.height - padding,
                ),
                "2": (
                    padding,
                    base_image.height - watermark.height - padding,
                ),
                "3": (
                    base_image.width - watermark.width - padding,
                    padding,
                ),
                "4": (padding, padding),
                "5": (
                    int((base_image.width - watermark.width) / 2),
                    int((base_image.height - watermark.height) / 2),
                ),
            }
            position = positions.get(options["position"], positions["1"])

            transparent_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
            transparent_layer.paste(watermark, position, mask=watermark)

            final_image = Image.alpha_composite(base_image, transparent_layer)

            final_image_bytes = io.BytesIO()
            final_image.convert("RGB").save(
                final_image_bytes, format="JPEG", quality=95
            )
            final_image_bytes.seek(0)
            final_image_bytes.name = "watermarked.jpg"

            return final_image_bytes

    except Exception as e:
        console.print(
            f"[red]Error processing image {os.path.basename(image_path)}: {e}[/red]"
        )
        return None


async def run(client: TelegramClient):
    """
    Orchestrates the process of applying a watermark to a folder of images and sending them.

    The workflow includes:
    1. Prompting for the source folder, watermark file, and destination chat.
    2. Prompting for customization options (position, scale, opacity).
    3. Finding all image files in the source folder.
    4. Iterating through each image, applying the watermark, and uploading it.
    5. Displaying progress and a final summary.

    Args:
        client (TelegramClient): The active and connected Telethon client instance.
    """
    console.clear()
    console.print(
        Panel(
            "[bold_italic medium_purple]Image Watermarker Module[/bold_italic medium_purple]"
        )
    )
    console.print(
        "[dim]Tip: For best results, use a transparent .png file as your watermark.[/dim]"
    )

    source_folder = Prompt.ask(
        "\n[bold]Enter the path to the folder with your source images[/bold]"
    )
    if not os.path.isdir(source_folder):
        console.print("[red]Error: The specified path is not a valid directory.[/red]")
        return

    watermark_path = Prompt.ask(
        "[bold]Enter the path to your watermark image file (e.g., logo.png)[/bold]"
    )
    if not os.path.isfile(watermark_path):
        console.print("[red]Error: The specified path is not a valid file.[/red]")
        return

    target_chat = await select_chat(
        client, "Select the chat to send the watermarked images to:"
    )
    if not target_chat:
        return

    console.print("\n[bold]Select a position for the watermark:[/bold]")
    console.print("[cyan]1[/cyan] - Bottom-Right [dim](Default)[/dim]")
    console.print("[cyan]2[/cyan] - Bottom-Left")
    console.print("[cyan]3[/cyan] - Top-Right")
    console.print("[cyan]4[/cyan] - Top-Left")
    console.print("[cyan]5[/cyan] - Center")
    position = Prompt.ask(
        "Enter your choice", choices=["1", "2", "3", "4", "5"], default="1"
    )

    scale = IntPrompt.ask("[bold]Watermark size (% of image width)[/bold]", default=15)
    opacity = IntPrompt.ask("[bold]Watermark opacity (1-100%)[/bold]", default=70)

    options = {"position": position, "scale": scale, "opacity": opacity}

    image_files = [
        f
        for f in os.listdir(source_folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not image_files:
        console.print(
            "[yellow]No image files (.png, .jpg, .jpeg) found in the specified folder.[/yellow]"
        )
        return

    console.print(
        f"\n[cyan]Found {len(image_files)} images. Preparing to process and upload...[/cyan]"
    )

    with Progress(console=console) as progress:
        task = progress.add_task("[purple]Processing images...", total=len(image_files))
        for filename in image_files:
            image_path = os.path.join(source_folder, filename)
            progress.update(
                task, description=f"[purple]Processing '{filename}'[/purple]"
            )

            final_image_bytes = apply_watermark(image_path, watermark_path, options)

            if final_image_bytes:
                progress.update(
                    task, description=f"[purple]Uploading '{filename}'[/purple]"
                )
                await client.send_file(
                    target_chat,
                    final_image_bytes,
                    force_document=False,
                    caption="",
                )

            progress.update(task, advance=1)

    console.print(f"\n[bold green]--- Process Complete ---[/bold green]")
    console.print(
        f"Successfully processed and uploaded {len(image_files)} images to '{target_chat.name}'."
    )
