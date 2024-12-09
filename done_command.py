import re
from file_reader_handler import getFilepath
from embedding_handler import get_openai_embedding
from milvus_handler import create_milvus_collection, insert_into_milvus
import discord
from discord import Intents, Client, Message, TextChannel
from discord import app_commands
from discord.ext import commands

# Solidity function parser
def parse_solidity_functions(code):
    function_pattern = re.compile(r'function\s+(\w+)\s*\(([^)]*)\)\s*([^{}]*)\{([^}]*)\}')
    
    functions = []
    matches = function_pattern.findall(code)
    for match in matches:
        function_name = match[0]
        parameters = match[1].strip()
        return_type = match[2].strip()
        body = match[3].strip()

        function_dict = {
            'full_function': f'function {function_name}({parameters}) {return_type} {{\n{body}\n}}',
            'type': 'solidity'
        }
        functions.append(function_dict)
    return functions

# Java function parser
def parse_java_functions(code):
    # This pattern captures public/private, return type, method name, parameters, and body
    function_pattern = re.compile(r'(public|private|protected)?\s*(static\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)\s*({[^}]*})')
    
    functions = []
    matches = function_pattern.findall(code)
    for match in matches:
        visibility = match[0].strip() if match[0] else ''
        static = match[1].strip() if match[1] else ''
        return_type = match[2].strip()
        function_name = match[3].strip()
        parameters = match[4].strip()
        body = match[5].strip()

        function_dict = {
            'full_function': f'{visibility} {static} {return_type} {function_name}({parameters}) {body}',
            'type': 'java'
        }
        functions.append(function_dict)
    return functions

# Generic function to detect and parse based on the code structure
def detect_and_parse_functions(code):
    if 'function' in code:  # Likely Solidity
        return parse_solidity_functions(code)
    else:
        return parse_java_functions(code)  # Assume Java if no 'function' keyword

async def process_and_insert_functions(file_data, interaction: discord.Interaction):
    create_milvus_collection(str(interaction.user.id), dimension=1536)  # Ensure collection is created or exists
    
    data = []
    id_counter = 0

    for file_name, content in file_data.items():
        # Detect and parse functions based on content, not extension
        functions = detect_and_parse_functions(content)
        
        if functions:
            for func in functions:
                embedding = get_openai_embedding(func['full_function'])
                if embedding is not None:
                    data.append({
                        "id": id_counter,
                        "vector": embedding.tolist(),  # Convert ndarray to list
                        "text": func['full_function'],
                        "subject": func['type']
                    })
                    id_counter += 1
                else:
                    print(f"Skipping a function in {file_name} due to embedding issues.")
        else:
            print(f"No functions found in {file_name}")

    if data:
        print(f"Preparing to insert {len(data)} records into Milvus.")
        insert_into_milvus(data, str(interaction.user.id))  # Call synchronously
    else:
        print("No records to insert into Milvus.")
    
async def getDownloadedFileFolder(folder_path, interaction: discord.Interaction):
        # Get the file content dictionary using getFilepath
    file_data = getFilepath(folder_path)
    
    # Process functions and insert them into Milvus
    await process_and_insert_functions(file_data, interaction)
    await interaction.followup.send("Success!! Your uploaded context is ready to use.", ephemeral=True)

# Process files and insert their context into Milvus
async def process_and_store_context(file_data, user_id, db_conn):
    create_milvus_collection(str(user_id), dimension=1536)  # Create or ensure collection exists
    data = []
    id_counter = 0

    for file_name, content in file_data.items():
        functions = detect_and_parse_functions(content)  # Detect and parse functions
        for func in functions:
            embedding = get_openai_embedding(func['full_function'])
            if embedding is not None and len(embedding) > 0:
                data.append({
                    "id": id_counter,
                    "vector": embedding.tolist(),
                    "text": func['full_function'],
                    "subject": func['type']
                })
                id_counter += 1

    if data:
        insert_into_milvus(data, str(user_id))
        print(f"Inserted {len(data)} records into Milvus for user {user_id}.")

if __name__ == "__main__":
    folder_path = 'ajna-core-2d6bbcb39a020a041d5243eadd8f4cb77e85c41b'  # Replace with your folder path

    # Get the file content dictionary using getFilepath
    file_data = getFilepath(folder_path)
    
    # Process functions and insert them into Milvus
    process_and_insert_functions(file_data)
