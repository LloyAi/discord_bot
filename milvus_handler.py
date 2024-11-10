from pymilvus import MilvusClient
import numpy as np
import json

# Initialize Milvus Client
client = MilvusClient("CodingAssistantMaster2.db")
# collection_name = "Faiss_App3"

def get_collection_name(user_id):
    """Helper function to get collection name from user ID."""
    return f"_{user_id}"

def create_milvus_collection(User_id, dimension=1536):
    
    collection_name = get_collection_name(User_id)
    if not client.has_collection(collection_name=collection_name):
        # Create the collection with the dimension specified and no specific fields
        client.create_collection(
            collection_name=collection_name,
            dimension=dimension,
        )
        print ("just created collection: " + collection_name)
    else:
        print("collection name: " +  User_id)

def insert_into_milvus(data, User_Id):

    collection_name = get_collection_name(User_Id)
    # Insert the embeddings as records directly into Milvus
    client.insert(
        collection_name=collection_name,
        data=data  # Directly pass the list of dictionaries
    )
    # After insertion, print the number of entities in the collection
    print(f"Inserted {len(data)} records into the collection '{collection_name}'.")

def query_milvus(query_embedding, User_id, limit=5):
    collection_name = get_collection_name(User_id)
    # Ensure the query_embedding is a list of floats
    if not isinstance(query_embedding, np.ndarray):
        query_embedding = np.array(query_embedding, dtype=float)
    else:
        query_embedding = query_embedding.astype(float)
    
    # Wrap the embedding in a list if it's not already
    query_embedding = query_embedding.tolist()
    if not client.has_collection(collection_name=collection_name):
        create_milvus_collection(User_id, dimension=1536)
    
    search_res = client.search(
        collection_name=collection_name,
        data=query_embedding,
        limit=limit,
        output_fields=["text", "subject"]
    )
    print(search_res, type(search_res))
   
    ## similarity threshold (close to 0, more similar it is - over 0.02 seems irrelevant)
    threshold_dist = 0.02
    passes_threshold = True

    for data in search_res[0]:
        if data.get('distance') > threshold_dist:
            passes_threshold = False
            break
    return search_res, passes_threshold
