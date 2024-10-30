from openai import OpenAI
import json
import os
from typing_extensions import override
from openai import AssistantEventHandler
import re 
from dotenv import load_dotenv
import sys

load_dotenv()
# Initialize OpenAI Client
client = OpenAI(api_key= os.environ.get ("OPENAI_API_KEY"))


# File to save assistant data
ASSISTANT_FILE = "assistant.json"

# Global variable to store assistant responses
output_data = ""

# Save assistant and vector store ID to a file
def save_data(assistant_id, vector_store_id):
    with open(ASSISTANT_FILE, 'w') as f:
        json.dump({"assistant_id": assistant_id, "vector_store_id": vector_store_id}, f)

# Load assistant and vector store ID from the file
def load_data():
    if os.path.exists(ASSISTANT_FILE):
        with open(ASSISTANT_FILE, 'r') as f:
            data = json.load(f)
            return data.get("assistant_id"), data.get("vector_store_id")
    return None, None

# Step 1: Create an Assistant with File Search Enabled (or load if exists)
def create_or_load_assistant():
    assistant_id, _ = load_data()
    if assistant_id:
        print(f"Loaded existing assistant with ID: {assistant_id}")
        return client.beta.assistants.retrieve(assistant_id)
    
    # If no saved assistant, create a new one
    assistant = client.beta.assistants.create(
        name="Math Equation Image Extractor",
        instructions="You are an assistant that specializes in recognizing and extracting mathematical equations from images in a file and converting them to LaTeX.",
        model="gpt-4o",
        tools=[{"type": "file_search"}],
    )
    print(f"New assistant created with ID: {assistant.id}")
    return assistant

# Step 2: Create or Load the Vector Store and Upload Files
def create_or_load_vector_store(file_paths):
    _, vector_store_id = load_data()
    
    if vector_store_id:
        print(f"Loaded existing vector store with ID: {vector_store_id}")
        return client.beta.vector_stores.retrieve(vector_store_id)

    # Create a new vector store if it doesn't exist
    vector_store = client.beta.vector_stores.create(name="Documents")

    # Open the files for reading
    file_streams = [open(path, "rb") for path in file_paths]

    # Upload files and poll status until processing is complete
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    # Close the file streams after upload
    for stream in file_streams:
        stream.close()

    # Print the result of the file upload
    print("File Batch Status:", file_batch.status)
    print("File Counts:", file_batch.file_counts)

    return vector_store

# Step 3: Update Assistant with the Vector Store
def update_assistant_with_vector_store(assistant_id, vector_store_id):
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )
    return assistant

# Step 4: Start a conversation with the Assistant
def create_thread(query):
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query
    )
    return thread

# First, we create a EventHandler class to define
# how we want to handle the events in the response stream.
class EventHandler(AssistantEventHandler):    
  @override
  def on_text_created(self, text) -> None:
    global output_data
    output_data += f"\nassistant > "
    # print(f"\nassistant > ", end="", flush=True)
      
  @override
  def on_text_delta(self, delta, snapshot):
    global output_data
    output_data += delta.value
    # print(delta.value, end="", flush=True)
      
  def on_tool_call_created(self, tool_call):
    global output_data
    output_data += f"\nassistant > {tool_call.type}\n"
    # print(f"\nassistant > {tool_call.type}\n", flush=True)
  
  def on_tool_call_delta(self, delta, snapshot):
    global output_data
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        output_data += delta.code_interpreter.input
        # print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        output_data += f"\n\noutput >\n"
        # print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            # print(f"\n{output.logs}", flush=True)
            output_data += f"\n{output.logs}\n"

def extract_latex_equations(text):
    # Regular expression to extract LaTeX equations inside \[...\] blocks
    equation_pattern = r"\\\[(.*?)\\\]"

    # Find all equations in the input text
    equations = re.findall(equation_pattern, text, re.DOTALL)

    # Clean and process each equation (strip whitespace)
    equations = [eq.strip() for eq in equations]

    # Structure the output as a dictionary
    output_data = {"equations": equations}

    # Print the extracted data in JSON format
    output_json = json.dumps(output_data, indent=2)

    # Optionally save to a JSON file
    with open("equations_output.json", "w", encoding="utf-8") as f:
        f.write(output_json)

if __name__ == "__main__":
    # Step 1: Create or load the assistant
    assistant = create_or_load_assistant()

    # # Step 2: Upload files and create or load a vector store
    # file_paths = ["sample_docs/Whitepaper Highlighted.pdf"]   # Add your file paths here
    # vector_store = create_or_load_vector_store(file_paths)

    # Step 2: Get the file paths from command-line arguments
    file_paths = sys.argv[1:]  # Get all arguments passed after the script name
    print(file_paths)
    if not file_paths:
        raise ValueError("No PDF file paths provided. Please provide valid file paths as arguments.")
    vector_store = create_or_load_vector_store(file_paths)

    # Step 3: Save assistant and vector store data for persistence
    save_data(assistant.id, vector_store.id)

    # Step 4: Update assistant with the vector store
    updated_assistant = update_assistant_with_vector_store(assistant.id, vector_store.id)

    # Step 5: create a thread
    query = "Can you extract all the math equations that are images from each page and provide them in LaTeX?"
    thread = create_thread(query)

    with client.beta.threads.runs.stream(
        thread_id=thread.id,
        assistant_id=assistant.id,
        # instructions="Please address the user as Josh.",
        event_handler=EventHandler(),
        ) as stream:
        stream.until_done()
 
    extract_latex_equations(output_data)