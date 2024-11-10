import numpy as np
from embedding_handler import get_openai_embedding, client as openai_client
from milvus_handler import query_milvus, client as milvus_client

def getAiresponse(query_text, User_id):
    print("We just got the embedding")
    generated_response = "Sorry, I could not find any relevant information to respond to your query."  # Default response
    
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
                
                if passes_threshold:
                    # Generate a response using OpenAI's language model
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",  # Or any other model you prefer
                        messages=[
                            {"role": "system", "content": "You are a helpful assistant."},
                            {"role": "user", "content": f"Here is data: {full_context}."},
                            {"role": "user", "content": f"Based on the above data, please answer the following query: {query_text}."}
                        ]
                    )

                    print('logging- generted_context_res')
                    generated_response = response.choices[0].message.content.strip()
                else:
                    response = openai_client.chat.completions.create(
                    model="gpt-4o",  # Or any other model you prefer
                    messages=[
                        {"role": "system", "content": "You are a senior software engineer."},
                        {"role": "user", "content": f"Here is data: {full_context}."},
                        {"role": "user", "content": f"Please answer the following question: {query_text}."}
                    ]
                )
                    generated_response =  response.choices[0].message.content.strip()
                print(f'. {generated_response}')
            else:
                print("No relevant data found in the Milvus collection.")
        else:
            print("No relevant data found in the Milvus collection.")
    else:
        print("Query text exceeds token limit.")
    
    
    return generated_response
