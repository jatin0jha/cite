import discord
import os
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up bot with commands and intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

import re
from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests

def create_quote_image(user_avatar_url, message_content, user_display_name):
    """Creates a 16:9 image with the quoted message and user details."""
    # Define image dimensions (16:9 ratio)
    width, height = 1280, 720
    avatar_width = 400  # Width for the avatar section

    # Create a solid black background
    background = Image.new("RGBA", (width, height), (0, 0, 0, 255))

    # Load and process the avatar
    try:
        avatar = Image.open(requests.get(user_avatar_url, stream=True).raw).convert("RGBA")

        # Crop and resize the avatar to fit the left section
        avatar_aspect_ratio = avatar.width / avatar.height
        target_aspect_ratio = avatar_width / height

        if avatar_aspect_ratio > target_aspect_ratio:
            new_width = int(avatar.height * target_aspect_ratio)
            offset = (avatar.width - new_width) // 2
            avatar = avatar.crop((offset, 0, offset + new_width, avatar.height))
        else:
            new_height = int(avatar.width / target_aspect_ratio)
            offset = (avatar.height - new_height) // 2
            avatar = avatar.crop((0, offset, avatar.width, offset + new_height))

        avatar = avatar.resize((avatar_width, height))
    except Exception:
        avatar = Image.new("RGBA", (avatar_width, height), (100, 100, 100, 255))

    # Add gradient overlay
    gradient = Image.new("RGBA", (avatar_width, height), (0, 0, 0, 0))
    for x in range(avatar_width):
        alpha = int(255 * (x / avatar_width))
        for y in range(height):
            gradient.putpixel((x, y), (0, 0, 0, alpha))
    avatar = Image.alpha_composite(avatar, gradient)

    # Paste the avatar onto the background
    background.paste(avatar, (0, 0))

    # Add text
    draw = ImageDraw.Draw(background)
    text_x = avatar_width + 40

    # Font loading
    text_font_path = "Roboto-VariableFont_wdth,wght.ttf"  # Path to regular text font
    emoji_font_path = "NotoEmoji-VariableFont_wght.ttf"  # Path to emoji font
    try:
        font_quote = ImageFont.truetype(text_font_path, 40)
        font_emoji = ImageFont.truetype(emoji_font_path, 40)
        font_username = ImageFont.truetype(text_font_path, 30)
    except Exception as e:
        print(f"Font loading failed: {e}")
        return

    # Wrap the message content to fit within the available width
    max_width = width - avatar_width - 80
    wrapped_text = textwrap.wrap(message_content, width=30)

    # Calculate total text height for vertical centering
    total_text_height = sum(font_quote.getbbox(line)[3] for line in wrapped_text) + (len(wrapped_text) - 1) * 10
    text_y = (height - total_text_height) // 2

    # Regex to split text into words and emojis
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F1E0-\U0001F1FF"  # Flags
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed Characters
        "]+", flags=re.UNICODE
    )

    # Draw each line of text
    for line in wrapped_text:
        current_x = text_x
        for segment in re.split(f"({emoji_pattern.pattern})", line):
            if emoji_pattern.match(segment):  # Emoji
                draw.text((current_x, text_y), segment, fill="white", font=font_emoji, embedded_color=True)
                current_x += font_emoji.getlength(segment)
            else:  # Regular text
                draw.text((current_x, text_y), segment, fill="white", font=font_quote)
                current_x += font_quote.getlength(segment)
        text_y += font_quote.getbbox(line)[3] + 10

    # Draw the username below the text
    draw.text((text_x, text_y + 20), f'~ {user_display_name}', fill="white", font=font_username)

    # Save the image
    output_path = "quote_image.png"
    background.save(output_path)
    return output_path

# Sync command tree when bot is ready
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        print(f"Logged in as {bot.user}")
    except Exception as e:
        print(f"Error syncing commands: {e}")

# Context Menu Command (Right-click a message to quote it)
@bot.tree.context_menu(name="Quote Message")
async def quote_message(interaction: discord.Interaction, message: discord.Message):
    """Quotes the selected message."""
    await interaction.response.defer()  # Acknowledge interaction to avoid timeout
    
    try:
        user_avatar_url = message.author.avatar.url if message.author.avatar else None
        message_content = message.content
        user_display_name = message.author.display_name
        
        # Create the quote image
        image_path = create_quote_image(user_avatar_url, message_content, user_display_name)
        
        # Send the image
        await interaction.followup.send(file=discord.File(image_path))
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")

# Run the bot
bot.run(TOKEN)