import numpy as np
from embedding_handler import get_openai_embedding, client as openai_client
from milvus_handler import query_milvus, client as milvus_client

def getAiresponse(query_text, User_id, user_name, db_conn, use_theoriq_db, is_saved=False):

    def save_user_history(user_name, user_message, bot_response):
        print('Saving chat history in DB...')
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_history (user_name, user_message, bot_response) VALUES (%s, %s, %s)",
                (user_name, user_message, bot_response)
            )
            db_conn.commit()
    
    def fetch_user_history(user_name, limit=20):
        print('Fetching user history from DB...')
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT user_message, bot_response FROM user_history WHERE user_name = %s ORDER BY timestamp DESC LIMIT %s",
                (user_name, limit)
            )
            return cur.fetchall()

    print("We just got the embedding")
    generated_response = "Sorry, I could not find any relevant information to respond to your query."  # Default response
    
    # Fetch user history and format it
    history_context = ""
    if is_saved:
        chat_history = fetch_user_history(user_name)
        print('chat_history', chat_history)
        if chat_history:
            history_context = "\n".join(
                f"User: {msg}\nAssistant: {resp}" for msg, resp in reversed(chat_history)
            )

    # Get the embedding for the query text
    query_embedding = get_openai_embedding(query_text)

    if query_embedding is not None:
        # Query Milvus for relevant context
        query_result, passes_threshold = query_milvus(np.array([query_embedding]), User_id, limit=5, use_theoriq_db=use_theoriq_db)
        print("We found context")

        # Collect all matching functions' full text if any
        function_contexts = []
        if query_result:
            print('logging- query result')
            function_contexts = [result['entity']['text'] for result in query_result[0] if result.get('entity', {}).get('text')]

        # Combine all relevant functions into a single context string
        full_context = "\n\n".join(function_contexts) if function_contexts else "No relevant data found in the Milvus collection."

        # Prepare the messages for OpenAI API
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
        if history_context:
            messages.append({"role": "user", "content": f"Here is our conversation history:\n{history_context}"})
        
        if full_context != "No relevant data found in the Milvus collection.":
            messages.extend([
                {"role": "user", "content": f"Here is data: {full_context}."},
                {"role": "user", "content": f"Based on the above data, please answer the following query: {query_text}."}
            ])
        else:
            messages.append({"role": "user", "content": f"Please answer the following query: {query_text}."})

        # Generate the response using OpenAI API
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages
            )
            print('logging- generated_context_res')
            generated_response = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
        print(f"Generated Response: {generated_response}")
    else:
        print("Query text exceeds token limit.")

    if is_saved and generated_response != "Sorry, I could not find any relevant information to respond to your query.":
        save_user_history(user_name, query_text, generated_response)
    
    return generated_response
