from typing import Final, Dict
import os
import discord
from dotenv import load_dotenv
from discord import Intents, Client, Message, TextChannel
from discord.ext import commands
# from Discord_Googledrive import done
#from responses import get_response
#from docsbot_responses import get_docbot_response, extract_sources, extract_answer, generate_conversation_id
from ai_command import getAiresponse
from Discord_Googledrive2 import done,enter_email,upload
import json
from Discord_Googledrive2 import user_folders, create_drive_service, get_all_files_in_folder, download_file, download_folder
from db import *
from done_command import process_and_store_context
from utils import process_files_and_get_response

db_connection = connect_to_rds()

ajna_folder_link = "https://drive.google.com/drive/folders/1lnTwkJc_t0dOh0ZfqVh47j6WEHVZzp_F"

# Load token from a safe place
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
LOG_CHANNEL_ID: Final[int] = int(os.getenv('DISCORD_LOG_CHANNEL_ID'))

# BOT SETUP
# Intents so bot can respond
intents: Intents = discord.Intents.all()
intents.message_content = True
client = commands.Bot(command_prefix='/', intents=intents)

# Dictionary to store conversation IDs
conversation_ids: Dict[str, str] = {}

# Function to get or create a conversation ID
def get_id(username: str) -> str:
    if username not in conversation_ids:
       # conversation_ids[username] = generate_conversation_id()
        print(conversation_ids)
    return conversation_ids[username]

# Function to log messages
async def log_message(channel: TextChannel, user_mention: str, question: str, answer: str, sources: str) -> None:
    def truncate(content: str, limit: int = 1024) -> str:
        return content if len(content) <= limit else content[:limit - 3] + "..."

    event_embed = discord.Embed(title="**JoshPilot-AI**", description="Detailed logs and responses", color=discord.Color.green())
    event_embed.add_field(name="**Message User**", value=user_mention, inline=True)
    event_embed.add_field(name="**Question**", value=truncate(question), inline=True)
    event_embed.add_field(name="**Answer**", value=truncate(answer), inline=True)
    event_embed.add_field(name="**Sources**", value=truncate(sources), inline=True)
    await channel.send(embed=event_embed)

async def send_message(message: Message, user_message: str, username: str, userID: str) -> None:
    if not user_message:
        print('Message Empty because intents were not enabled')
        return
    
    is_private = user_message.startswith('?')
    if is_private:
        user_message = user_message[1:]
        await message.author.send("Processing...")
    else:
        await message.channel.send("Processing...")

    sources = "No sources found."
    try:
        if user_message.startswith('.AI'):
            #answer = get_response(user_message[3:].strip())
            answer = getAiresponse(user_message[3:].strip(), userID, username, db_connection, False)

        elif user_message.startswith('.Ajna'):
            answer = await process_files_and_get_response(user_message[5:].strip(), userID, username, db_connection)
            # print(user_message[5:].strip())
            # folder_id = "1lnTwkJc_t0dOh0ZfqVh47j6WEHVZzp_F"
            # service = create_drive_service()

            # files = get_all_files_in_folder(service, folder_id)
            # print(files)
            # if not files:
            #     print("No files found in the folder")
            #     return

            # destination_folder = "downloaded_files"
            # os.makedirs(destination_folder, exist_ok=True)

            # for file in files:
            #     file_id = file['id']
            #     file_name = file['name']
            #     mime_type = file['mimeType']
            #     print('file',file)
            #     if mime_type == 'application/vnd.google-apps.folder':
            #         items = get_all_files_in_folder(service, file_id)
            #         print('items',items)
            #         download_folder(service, file_id, file_name, destination_folder)
            #     else:
            #         download_file(service, file_id, destination_folder, file_name)

            # file_data = {}
            # for root, _, files in os.walk(destination_folder):  # Walk through folders and files
            #     for file_name in files:  # Only process files, not directories
            #         file_path = os.path.join(root, file_name)
            #         try:
            #             # Open and read the file with error handling for decoding issues
            #             with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            #                 file_data[file_name] = file.read()
            #         except Exception as e:
            #             print(f"Error reading file {file_name}: {e}")

            # for root, dirs, files in os.walk(destination_folder):
            #     print(f"Current Directory: {root}")
            #     print(f"Subdirectories: {dirs}")
            #     print(f"Files: {files}")
                
            # await process_and_store_context(file_data, userID, db_connection)

            # print("Context processed and stored successfully!")
            # answer = getAiresponse(user_message[5:].strip(), userID, username, db_connection, is_saved=True)
        else:
            convo_id = get_id(username)
           # response_json = get_docbot_response(user_message[4:].strip(), convo_id)

            #if "error" not in response_json:
           #     sources = extract_sources(response_json)
            #    answer = extract_answer(response_json)
           # else:
             #   answer = "Error occurred while processing the request."

        print(sources)

        # Split the response into chunks of 2000 characters or less
        response_chunks = []
        while len(answer) > 2000:
            split_point = answer[:2000].rfind(' ')
            if split_point == -1:
                split_point = 2000
            response_chunks.append(answer[:split_point])
            answer = answer[split_point:].strip()
        response_chunks.append(answer)

        # Send each chunk as a separate message
        for chunk in response_chunks:
            if is_private:
                await message.author.send(chunk)
            else:
                await message.channel.send(chunk)
        
        # Log the question and answer
        log_channel = client.get_channel(LOG_CHANNEL_ID)
        await log_message(log_channel, message.author.mention, user_message, "\n".join(response_chunks), sources)
        
    except Exception as e:
        print(f'Error: {e}')
        if is_private:
            await message.author.send(f"An error occurred")
        else:
            await message.channel.send(f"An error occurred")

# Handling the startup for the bot      
@client.event
async def on_ready() -> None:
    if db_connection:
        print("Database connected!")
    else:
        print("Failed to connect to the database.")
    await client.tree.sync()
    print(f'{client.user} is now running!')

# Combined event to handle both messages and file uploads
@client.event
async def on_message(message: Message) -> None:
    # For the bot to not respond to itself
    if message.author == client.user:
        return
    
    user_message = message.content


    # Check if the message contains a command or is a file upload
    if user_message.startswith(('.AI', '.bot','.Ajna')):
        username = str(message.author)
        channel = str(message.channel)
        user_id = str(message.author.id)
        print("userId: "+  user_id)
        
        print(f'[{channel}] {username}: "{user_message}"')
        
        await send_message(message, user_message, username, user_id)

    # elif message.attachments and not message.author.bot:
    #     # Handle file upload and send the file URL back to the user
    #     attachment = message.attachments[0]
    #     file_url = attachment.url
    #     await message.channel.send(f'File uploaded successfully! You can access it here: {file_url}')

    # Ensuring the bot processes commands even after an on_message event
    await client.process_commands(message)
        
@client.tree.command(name="hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"hey {interaction.user.mention}! This is a slash command!",
        ephemeral=True
    )

@client.tree.command(name="enter_email", description="Enter your email to receive file links")
async def command_enter_email(interaction: discord.Interaction, email: str):
    await interaction.response.defer(ephemeral=True)  # Defer the interaction
    folder_Link = await enter_email(interaction, email)
    await interaction.followup.send(folder_Link, ephemeral=True)  # Send the follow-up message



       

# # Slash command for initiating the file upload
# @client.tree.command(name="upload", description="Upload a file and get the link")
# async def upload(interaction: discord.Interaction):
#     await interaction.response.send_message('Please upload your file.')


  
# Slash command for initiating the file upload
@client.tree.command(name="upload", description="Upload a file and get the Google Drive link")
async def command_upload(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # Defer the interaction to avoid timeouts
    folder_Link = await upload(interaction)  # Await the upload coroutine
    print(folder_Link)
    await interaction.followup.send(folder_Link, ephemeral=True)  # Send the follow-up message



# Slash command to trigger the main function
@client.tree.command(name="done", description="Trigger the main function")
async def command_done(interaction: discord.Interaction):
    #await interaction.response.defer(ephemeral=True)  # Defer the interaction
    await interaction.response.send_message("Indexing Files...\nWe will send a message when your context is ready.", ephemeral=True)  # Send initial response
    await done(interaction)  # Run the main function

@client.tree.command(name="extract_equations", description="Extract LaTeX equations from PDF")
async def command_extract_equations(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # Defer the interaction
    
    user_id = interaction.user.id
    folder_info = user_folders.get(user_id)

    if not folder_info:
        return await interaction.followup.send("No downloaded files found. Please upload files first.", ephemeral=True)
    

    folder_path = folder_info["child_folder_name"]
    script_directory = os.path.dirname(os.path.abspath(__file__))
    pdf_folder_path = os.path.join(script_directory, folder_path)
    
    # Collect all PDF file paths from the directory
    pdf_files = [os.path.join(pdf_folder_path, f) for f in os.listdir(pdf_folder_path) if f.endswith('.pdf')]
    if not pdf_files:
            return await interaction.followup.send("No PDF files found in the specified folder.", ephemeral=True)
    

    try:
        # Call your script's main function here
        await interaction.followup.send("Extracting equations from PDF...")

        # os.system('python3 extract_equations.py')
        os.system(f'python3 extract_equations.py {" ".join(pdf_files)}')

        # After the script runs, send the results
        with open("equations_output.json", "r") as f:
            equations_data = json.load(f)

        # Format and send the results
        equations_message = f"Extracted LaTeX Equations:\n{equations_data}"
        await interaction.followup.send(equations_message, ephemeral=True)
    
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@client.tree.command(name="status", description="Number of users in database")
# Command to display the number of users
async def status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # Defer the interaction to avoid timeouts
    # Count the number of users across all guilds (servers) the bot is in
    user_count = get_user_count(db_connection)
    await interaction.followup.send(f"The bot is currently serving {user_count} users.", ephemeral=True)

# Start the bot
def main() -> None:
    client.run(TOKEN)

if __name__ == '__main__':
    main()
