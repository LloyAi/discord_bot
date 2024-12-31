import os
from Discord_Googledrive2 import create_drive_service, get_all_files_in_folder, download_file, download_folder
from ai_command import getAiresponse
from done_command import process_and_store_context

async def process_files_and_get_response(user_message, userID, username, db_connection):
    """
    Function to process files in Google Drive, extract context, and return AI response.
    """
    folder_id = "1lnTwkJc_t0dOh0ZfqVh47j6WEHVZzp_F"
    service = create_drive_service()

    files = get_all_files_in_folder(service, folder_id)
    if not files:
        return "No files found in the folder."

    destination_folder = "downloaded_files"
    os.makedirs(destination_folder, exist_ok=True)

    for file in files:
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']
        if mime_type == 'application/vnd.google-apps.folder':
            items = get_all_files_in_folder(service, file_id)
            download_folder(service, file_id, file_name, destination_folder)
        else:
            download_file(service, file_id, destination_folder, file_name)

    file_data = {}
    for root, _, files in os.walk(destination_folder):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    file_data[file_name] = file.read()
            except Exception as e:
                print(f"Error reading file {file_name}: {e}")

    await process_and_store_context(file_data, userID, db_connection)

    answer = getAiresponse(user_message, userID, username, db_connection, is_saved=True)
    return answer
