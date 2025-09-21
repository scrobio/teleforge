# -*- coding: utf-8 -*-
"""
Image Watermarker Module - Teleforge

This module provides a powerful tool for content creators to apply a
watermark to a batch of images and upload them directly to a Telegram chat.
It supports both image-based (e.g., a logo) and text-based watermarks,
offering customization options for position, scale, and opacity.
"""
import io
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import IntPrompt, Prompt
from telethon.sync import TelegramClient

from utils.chat_selector import select_chat

console = Console()

try:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "arial.ttf"
except NameError:
    # Fallback for some environments where __file__ might not be defined
    FONT_PATH = "assets/fonts/arial.ttf"


def create_text_watermark_image(
    text: str, size: tuple, font_path: str, opacity: int, scale: float
) -> Image.Image | None:
    """
    Creates an in-memory Pillow Image of a text watermark.

    Args:
        text (str): The text content of the watermark.
        size (tuple): The (width, height) of the base image to scale against.
        font_path (str): The file path to the .ttf or .otf font file.
        opacity (int): The desired opacity percentage (0-100).
        scale (float): The desired font size, calculated as a percentage of the image width.

    Returns:
        Image.Image | None: A Pillow Image object of the rendered text, or None on error.
    """
    try:
        font_size = int((size[0] * (scale / 100)) / len(text) * 1.8)
        font = ImageFont.truetype(font_path, font_size)

        temp_draw = ImageDraw.Draw(Image.new("RGBA", (0, 0)))
        text_bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        watermark_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_img)

        fill_opacity = int(255 * (opacity / 100))
        fill_color = (255, 255, 255, fill_opacity)

        stroke_opacity = int(255 * (opacity / 100))
        stroke_color = (0, 0, 0, stroke_opacity)

        stroke_width = max(1, int(font_size / 25))

        draw.text(
            (0, -text_bbox[1]),
            text,
            font=font,
            fill=fill_color,
            stroke_width=stroke_width,
            stroke_fill=stroke_color,
        )

        return watermark_img

    except FileNotFoundError:
        console.print(
            f"[red]Error: Font file not found at '{font_path}'. Please check the FONT_PATH variable.[/red]"
        )
        return None
    except Exception as e:
        console.print(f"[red]Error creating text watermark: {e}[/red]")
        return None


def apply_watermark(
    image_path: str, watermark_asset: str | Image.Image, options: dict
) -> io.BytesIO | None:
    """
    Applies a watermark (either an image or text) to a base image.

    Args:
        image_path (str): File path to the base image.
        watermark_asset (str | Image.Image): Either a file path to the watermark image
            or a pre-rendered Pillow Image object (for text watermarks).
        options (dict): A dictionary containing customization settings.

    Returns:
        io.BytesIO | None: An in-memory bytes object of the final watermarked image,
        or None if an error occurred.
    """
    try:
        with Image.open(image_path).convert("RGBA") as base_image:
            final_watermark: Image.Image

            # Process image-based watermark.
            if isinstance(watermark_asset, str):
                with Image.open(watermark_asset).convert("RGBA") as img_watermark:
                    ratio = img_watermark.height / img_watermark.width
                    new_width = int(base_image.width * (options["scale"] / 100))
                    final_watermark = img_watermark.resize(
                        (new_width, int(new_width * ratio)), Image.Resampling.LANCZOS
                    )
                    if options["opacity"] < 100:
                        alpha = final_watermark.getchannel("A").point(
                            lambda p: p * (options["opacity"] / 100)
                        )
                        final_watermark.putalpha(alpha)
            # Use the pre-rendered text watermark image.
            else:
                final_watermark = watermark_asset

            # Determine position. Text watermark is always centered.
            padding = 10
            if options["type"] == "text":
                position = (
                    int((base_image.width - final_watermark.width) / 2),
                    int((base_image.height - final_watermark.height) / 2),
                )
            else:
                positions = {
                    "1": (
                        base_image.width - final_watermark.width - padding,
                        base_image.height - final_watermark.height - padding,
                    ),
                    "2": (
                        padding,
                        base_image.height - final_watermark.height - padding,
                    ),
                    "3": (base_image.width - final_watermark.width - padding, padding),
                    "4": (padding, padding),
                    "5": (
                        int((base_image.width - final_watermark.width) / 2),
                        int((base_image.height - final_watermark.height) / 2),
                    ),
                }
                position = positions.get(options["position"], positions["1"])

            # Composite the watermark onto the base image.
            transparent_layer = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
            transparent_layer.paste(final_watermark, position, mask=final_watermark)
            final_image = Image.alpha_composite(base_image, transparent_layer)

            # Save the final image to an in-memory bytes object.
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
    Orchestrates applying a watermark to a folder of images and sending them.
    """
    console.clear()
    console.print(
        Panel(
            "[bold_italic medium_purple]Image Watermarker Module[/bold_italic medium_purple]"
        )
    )

    source_folder = Prompt.ask(
        "\n[bold]Enter the path to the folder with your source images[/bold]"
    )
    if not os.path.isdir(source_folder):
        console.print("[red]Error: The specified path is not a valid directory.[/red]")
        return

    # Choose watermark type and get specific options.
    console.print("\n[bold]Select watermark type:[/bold]")
    console.print("[cyan]1[/cyan] - Text Watermark (e.g., @mychannel)")
    console.print("[cyan]2[/cyan] - Image Watermark (e.g., logo.png)")
    watermark_type_choice = Prompt.ask(
        "Enter your choice", choices=["1", "2"], default="1"
    )

    watermark_asset = None
    watermark_options = {}

    if watermark_type_choice == "1":  # Text
        watermark_options["type"] = "text"
        watermark_asset = Prompt.ask("[bold]Enter the text for the watermark[/bold]")
        watermark_options["scale"] = IntPrompt.ask(
            "[bold]Text size (approx. % of image width)[/bold]", default=25
        )
        watermark_options["opacity"] = IntPrompt.ask(
            "[bold]Text opacity (1-100%)[/bold]", default=50
        )

    else:  # Image
        watermark_options["type"] = "image"
        watermark_asset = Prompt.ask(
            "[bold]Enter the path to your watermark image file (e.g., logo.png)[/bold]"
        )
        if not os.path.isfile(watermark_asset):
            console.print("[red]Error: The specified path is not a valid file.[/red]")
            return

        console.print("\n[bold]Select a position for the image watermark:[/bold]")
        console.print(
            "[cyan]1[/cyan] - Bottom-Right [dim](Default)[/dim]",
            "  [cyan]2[/cyan] - Bottom-Left",
            "  [cyan]3[/cyan] - Top-Right",
        )
        console.print("[cyan]4[/cyan] - Top-Left", "        [cyan]5[/cyan] - Center")
        watermark_options["position"] = Prompt.ask(
            "Enter position choice", choices=["1", "2", "3", "4", "5"], default="1"
        )
        watermark_options["scale"] = IntPrompt.ask(
            "[bold]Watermark image size (% of image width)[/bold]", default=15
        )
        watermark_options["opacity"] = IntPrompt.ask(
            "[bold]Watermark image opacity (1-100%)[/bold]", default=70
        )

    target_chat = await select_chat(
        client, "Select the chat to send the watermarked images to:"
    )
    if not target_chat:
        return

    # Find and process images.
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

            watermark_to_apply = watermark_asset
            if watermark_options["type"] == "text":
                with Image.open(image_path) as img:
                    watermark_to_apply = create_text_watermark_image(
                        watermark_asset,
                        img.size,
                        FONT_PATH,
                        watermark_options["opacity"],
                        watermark_options["scale"],
                    )
                if not watermark_to_apply:
                    continue

            final_image_bytes = apply_watermark(
                image_path, watermark_to_apply, watermark_options
            )

            if final_image_bytes:
                progress.update(
                    task, description=f"[purple]Uploading '{filename}'[/purple]"
                )
                await client.send_file(
                    target_chat, final_image_bytes, force_document=False, caption=""
                )

            progress.update(task, advance=1)

    console.print(f"\n[bold green]--- Process Complete ---[/bold green]")
    console.print(
        f"Successfully processed and uploaded {len(image_files)} images to '{target_chat.name}'."
    )
