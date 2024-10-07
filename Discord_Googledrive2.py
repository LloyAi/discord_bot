from typing import Final, Dict, Optional
import os
from urllib.error import HTTPError
import discord
from dotenv import load_dotenv
from discord import Intents
from discord.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
#from file_con_adv_PDFfunction import getFilepath
from done_command import getDownloadedFileFolder
from datetime import datetime  # Import datetime module
import time


# Load token from a safe place
# load_dotenv()
# TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
# LOG_CHANNEL_ID: Final[int] = int(os.getenv('DISCORD_LOG_CHANNEL_ID'))

# # BOT SETUP
# intents: Intents = discord.Intents.all()
# intents.message_content = True
# client = commands.Bot(command_prefix='/', intents=intents)

# Dictionary to store user IDs and emails
user_emails: Dict[int, str] = {}

# Dictionary to store folder information
user_folders: Dict[int, Dict[str, str]] = {}

# Path to the service account JSON file
GOOGLE_DRIVE_CREDENTIALS = r"bot-testing-433504-1b047b5aa458.json"

# Initialize the Google Drive API service
def create_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)

# Function to download a file from Google Drive
def download_file(service, file_id, destination_folder, file_name):
    # Ensure the destination directory exists
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    destination_path = os.path.join(destination_folder, file_name)

    # Handle the case where `destination_path` might be a directory
    if os.path.isdir(destination_path):
        raise IsADirectoryError(f"Destination path '{destination_path}' is a directory.")

    request = service.files().get_media(fileId=file_id)

    with open(destination_path, 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")
        
    # Check the file paths
    print(f"Downloaded {file_name} to {destination_path}")

  

# Function to read folder metadata
def read_folder_metadata(service, folder_id):
    query = f"'{folder_id}' in parents"
    response = service.files().list(q=query, fields="nextPageToken, files(id, name, mimeType)").execute()
    return response.get('files', [])

# Function to select a folder by name
def select_folder_by_name(service, folder_name):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'"
    response = service.files().list(q=query, fields="files(id, name)").execute()
    folders = response.get('files', [])
    return folders[0] if folders else None

# Function to handle pagination in folder metadata
def get_all_files_in_folder(service, folder_id):
    files = []
    query = f"'{folder_id}' in parents"
    page_token = None
    while True:
        response = service.files().list(
            q=query, 
            fields="nextPageToken, files(id, name)", 
            pageSize=100, 
            pageToken=page_token
        ).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files

# Function to create a folder in Google Drive
def create_folder(service, name, parent_id=None):
    folder_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
    }
    if parent_id:
        folder_metadata['parents'] = [parent_id]

    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder['id']

# Function to share a folder with a specific email
def share_folder(service, folder_id, email):
    permission = {
        'role': 'writer',
        'type': 'user',
        'emailAddress': email,
    }
    service.permissions().create(fileId=folder_id, body=permission).execute()

# Function to get the URL of a folder
def get_folder_url(service, folder_id):
    folder = service.files().get(fileId=folder_id, fields='webViewLink').execute()
    return folder.get('webViewLink')

# Slash command to set the user's email and create a folder if needed
#@client.tree.command(name="enter_email", description="Enter your email to receive file links")
async def enter_email(interaction: discord.Interaction, email: str):
    user_id = interaction.user.id
    user_emails[user_id] = email

    # Initialize the Drive API service
    service = create_drive_service()

    # Create the parent and child folders
    parent_folder_name = f"Parent Folder for {interaction.user.name}"
    parent_folder_id = create_folder(service, parent_folder_name)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    child_folder_name = f"{interaction.user.name}_{timestamp}"
    child_folder_id = create_folder(service, child_folder_name, parent_folder_id)

    # Share the child folder with the user
    share_folder(service, child_folder_id, email)
    print("Folder ID: " + child_folder_id)
    print("Folder name " + child_folder_name)
    
    # Store the folder info
    user_folders[user_id] = {
        "child_folder_name": child_folder_name,
        "child_folder_id": child_folder_id
    }

    # Get the URL of the child folder
    folder_url = get_folder_url(service, child_folder_id)

    # Send the URL to the user
    return(f"Email set to {email}. Folder created and shared! You can access it here: {folder_url}")
    
# Slash command for initiating the file upload
#@client.tree.command(name="upload", description="Upload a file and get the Google Drive link")
async def upload(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Check if the user's email is set
    if user_id not in user_emails:
        return("Please set your email first using the /enter_email command.")
        

    email = user_emails[user_id]

    # Initialize the Drive API service
    service = create_drive_service()

    # Create the parent and child folders
    parent_folder_name = f"Parent Folder for {interaction.user.name}"
    parent_folder_id = create_folder(service, parent_folder_name)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    child_folder_name = f"{interaction.user.name}_{timestamp}"
    child_folder_id = create_folder(service, child_folder_name, parent_folder_id)

    # Share the child folder with the user
    share_folder(service, child_folder_id, email)
    print("Folder ID: " + child_folder_id)
    print("Folder name " + child_folder_name)
    
    # Store the folder info
    user_folders[user_id] = {
        "child_folder_name": child_folder_name,
        "child_folder_id": child_folder_id
    }

    # Get the URL of the child folder
    folder_url = get_folder_url(service, child_folder_id)

    # Send the URL to the user
    return(f"Folder created and shared! You can access it here: {folder_url}")

# Function to download a folder and its contents from Google Drive
def download_folder(service, folder_id, folder_name, parent_folder):
    # Create a new path for the destination folder
    new_destination_folder = os.path.join(parent_folder, folder_name)

    # Ensure the destination directory exists
    if not os.path.exists(new_destination_folder):
        os.makedirs(new_destination_folder)

    # List all files in the folder
    items = read_folder_metadata(service, folder_id)

    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            # Recursively download the subfolder
            download_folder(service, item['id'], item['name'], new_destination_folder)
        else:
            # Download the file to the new destination folder
            download_file(service, item['id'], new_destination_folder, item['name'])


# Slash command to trigger the main function
#@client.tree.command(name="done", description="Trigger the main function")
async def done(interaction: discord.Interaction):
    user_id = interaction.user.id

    # Retrieve the user's email and folder info
    email = user_emails.get(user_id)
    folder_info = user_folders.get(user_id)
    if not email or not folder_info:
        return await interaction.response.send_message("Please set your email and create/upload to a folder first.")
        
    # Initialize the Google Drive API service
    service = create_drive_service()

    # Set Folder_Id and Folder_Name
    Folder_Id = folder_info["child_folder_id"]
    Folder_Name = folder_info["child_folder_name"]

    # Run the main function logic
    destination_folder = Folder_Name  # Destination folder name

    # Create the full path for the destination folder
    script_directory = os.path.dirname(os.path.abspath(__file__))
    destination_path = os.path.join(script_directory, destination_folder)

    # Ensure the destination directory exists
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    # Get all files in the specified folder
    files = get_all_files_in_folder(service, Folder_Id)

    if not files:
        return await interaction.response.send_message("No files found or folder is inaccessible.")

    # Download each file or folder
    for file in files:
        file_id = file['id']
        file_name = file['name']
        item = service.files().get(fileId=file_id, fields='id, name, mimeType').execute()

        if item['mimeType'] == 'application/vnd.google-apps.folder':
            download_folder(service, file_id, item['name'], destination_path)
        else:
            download_file(service, item['id'], destination_path, item['name'])

    await getDownloadedFileFolder(destination_folder, interaction)

    
  

   





#def main() -> None:
  #  client.run(TOKEN)
    # # Initialize the Google Drive API service
    #  service = create_drive_service()
    #  Folder_Id = "17zHyUgPumOhk0Bniz8K6-NIgTjtHJSNO"
    #  Folder_Name = "ihatethisfor_20240829005152"
    #  destination_folder = Folder_Name  # Destination folder name

    # # Ensure the folder exists
    #  if not os.path.exists(destination_folder):
    #       os.makedirs(destination_folder)

    # # # Get all files in the specified folder
    #  files = get_all_files_in_folder(service, Folder_Id)

    #       # Print the files in the folder
    #  if files:
    #         print("Files in the folder:", files)
    #  else:
    #         print("No files found or folder is inaccessible.")

    # # Download each file
    # for file in files:
    #     file_id = file['id']
    #     file_name = file['name']
    #     # Download file to the specified destination folder
    #     download_file(service, file_id, destination_folder, file_name)
    #    # print(f"Downloaded {file_name} (ID: {file_id}) to {destination_folder}")

    # # Optionally, if you want to check the file paths
    # getFilepath(destination_folder)
   




#if __name__ == '__main__':
#   main()