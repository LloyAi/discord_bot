import numpy as np
from embedding_handler import get_openai_embedding, client as openai_client
from milvus_handler import query_milvus, client as milvus_client

def getAiresponse(query_text, User_id, user_name, db_conn):

    def save_user_history(user_name, user_message, bot_response):
        print('Saving chat history in DB...')
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_history (user_name, user_message, bot_response) VALUES (%s, %s, %s)",
                (user_name, user_message, bot_response )
            )
            db_conn.commit()
    
    def fetch_user_history(user_name, limit=10):
        print('Fetching user history from DB...')
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT user_message, bot_response FROM chat_history WHERE user_name = %s ORDER BY timestamp DESC LIMIT %s",
                (user_name, limit)
            )
            return cur.fetchall()

    print("We just got the embedding")
    generated_response = "Sorry, I could not find any relevant information to respond to your query."  # Default response
    
    # Fetch user history and format it
    chat_history = fetch_user_history(user_name)
    print('chat_history',chat_history)
    if chat_history:
        history_context = "\n".join(
            f"User: {msg}\nAssistant: {resp}" for msg, resp in reversed(chat_history)
        )
    else:
        history_context = ""

    # Get the embedding for the query text
    query_embedding = get_openai_embedding(query_text)
    
    if query_embedding is not None:
        # Query Milvus for relevant context
        query_result, passes_threshold = query_milvus(np.array([query_embedding]), User_id, limit=5)
        print("We found context")
        
        if query_result:
            print('logging- query result')
            # Collect all matching functions' full text
            function_contexts = [result['entity']['text'] for result in query_result[0] if result.get('entity', {}).get('text')]
            
            if function_contexts:
                print('logging- function_contexts')
                # Combine all relevant functions into a single context string
                full_context = "\n\n".join(function_contexts)
                messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                ]
                if history_context:
                    messages.append({"role": "user", "content": f"Here is our conversation history:\n{history_context}"})
                
                messages.extend([
                    {"role": "user", "content": f"Here is data: {full_context}."},
                    {"role": "user", "content": f"Based on the above data, please answer the following query: {query_text}."}
                ])

                # response = openai_client.chat.completions.create(
                #     model="gpt-4",  # Or any other model you prefer
                #     messages=messages
                # )

                if passes_threshold:
                    # Generate a response using OpenAI's language model
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",  # Or any other model you prefer
                        messages=messages
                    )

                    print('logging- generted_context_res')
                    generated_response = response.choices[0].message.content.strip()
                else:
                    response = openai_client.chat.completions.create(
                    model="gpt-4o",  # Or any other model you prefer
                    messages=messages
                )
                    generated_response =  response.choices[0].message.content.strip()
                print(f'. {generated_response}')
            else:
                print("No relevant data found in the Milvus collection.")
        else:
            print("No relevant data found in the Milvus collection.")
    else:
        print("Query text exceeds token limit.")

    if 'josh' in user_name:
        save_user_history(user_name, query_text, generated_response)
    
    return generated_response
