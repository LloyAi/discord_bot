import tiktoken
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()
# Initialize OpenAI Client
client = OpenAI(api_key= os.environ.get ("OPENAI_API_KEY"))

def get_openai_embedding(text, max_tokens=8192):
    tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = tokenizer.encode(text)

    if len(tokens) > max_tokens:
        return None  # Skip embedding if it exceeds the token limit

    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )

    embedding = response.data[0].embedding
    return np.array(embedding, dtype='float32')
