from pymilvus import MilvusClient, exceptions
import numpy as np
import json
import time
import threading

# Initialize Milvus Client
# client = MilvusClient("CodingAssistantMaster2.db")
# collection_name = "Faiss_App3"


# def retry_operation(func, *args, retries=3, wait_time=2, **kwargs):
#     """Function to retry an operation with specified retries and wait time."""
#     attempt = 0
#     while attempt < retries:
#         try:
#             return func(*args, **kwargs)
#         except Exception as e:
#             print(f"Attempt {attempt+1} failed with error: {e}")
#             attempt += 1
#             time.sleep(wait_time)
#     print(f"Failed after {retries} attempts.")
#     return None

class MilvusHandler:
    def __init__(self, db_file):
        self.db_file = db_file
        self.client = None
        self.lock = threading.Lock()  # Ensures thread-safe access to the client

    def get_collection_name(self, user_id):
        """Helper function to get collection name from user ID."""
        return f"_{user_id}"

    def create_connection(self):
        retries = 5
        wait_time = 2  # Start with 2 seconds
        for _ in range(retries):
            try:
                # If the client is already created, no need to reinitialize
                if self.client is None:
                    self.client = MilvusClient(self.db_file)
                return self.client
            except exceptions.ConnectionConfigException as e:
                print(f"Error: {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2  # Exponential backoff
        raise Exception(f"Failed to connect to Milvus after {retries} retries.")

    def retry_operation(self, operation_func, *args, **kwargs):
        """
        Retry logic for any operation involving the Milvus client.
        The lock is only applied during the critical function execution.
        """
        retries = 5
        wait_time = 2  # Start with 2 seconds
        for _ in range(retries):
            try:
                # Ensure the client is connected before executing the operation
                self.create_connection()

                with self.lock:  # Lock the database only for the operation
                    return operation_func(*args, **kwargs)

            except exceptions.ConnectionConfigException as e:
                print(f"Error: {e}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                wait_time *= 2  # Exponential backoff
        raise Exception(f"Failed to execute operation after {retries} retries.")

    def create_milvus_collection(self, User_id, dimension=1536):
        collection_name = self.get_collection_name(User_id)
        if not self.client.has_collection(collection_name=collection_name):
            # Create the collection with the dimension specified and no specific fields
            self.retry_operation(self.client.create_collection, 
                                 collection_name=collection_name, 
                                 dimension=dimension)
            print("Just created collection:", collection_name)
        else:
            print("Collection already exists:", collection_name)

    def insert_into_milvus(self, data, User_Id):
        collection_name = self.get_collection_name(User_Id)
        # Insert the embeddings as records directly into Milvus
        self.retry_operation(self.client.insert,
                             collection_name=collection_name,
                             data=data)
        print(f"Inserted {len(data)} records into the collection '{collection_name}'.")

    def query_milvus(self, query_embedding, User_id, limit=5):
        collection_name = self.get_collection_name(User_id)
        # Ensure the query_embedding is a list of floats
        if not isinstance(query_embedding, np.ndarray):
            query_embedding = np.array(query_embedding, dtype=float)
        else:
            query_embedding = query_embedding.astype(float)

        query_embedding = query_embedding.tolist()
        
        if not self.client.has_collection(collection_name=collection_name):
            self.create_milvus_collection(User_id, dimension=1536)
        
        # Perform the search with retry logic
        search_res = self.retry_operation(self.client.search,
                                          collection_name=collection_name,
                                          data=query_embedding,
                                          limit=limit,
                                          output_fields=["text", "subject"])
        
        # similarity threshold (close to 0, more similar it is - over 0.02 seems irrelevant)
        threshold_dist = 0.02
        passes_threshold = True

        for data in search_res[0]:
            if data.get('distance') > threshold_dist:
                passes_threshold = False
                break
        return search_res, passes_threshold
    
# def create_milvus_collection(User_id, dimension=1536):
    
#     collection_name = get_collection_name(User_id)
#     if not client.has_collection(collection_name=collection_name):
#         # Create the collection with the dimension specified and no specific fields
#         # client.create_collection(
#         #     collection_name=collection_name,
#         #     dimension=dimension,
#         # )
#         retry_operation(client.create_collection, 
#                         collection_name=collection_name, 
#                         dimension=dimension)
#         print ("just created collection: " + collection_name)
#     else:
#         print("collection name: " +  User_id)

# def insert_into_milvus(data, User_Id):

#     collection_name = get_collection_name(User_Id)
#     # Insert the embeddings as records directly into Milvus
#     # client.insert(
#     #     collection_name=collection_name,
#     #     data=data  # Directly pass the list of dictionaries
#     # )
#     retry_operation(client.insert,
#                     collection_name=collection_name,
#                     data=data)
#     # After insertion, print the number of entities in the collection
#     print(f"Inserted {len(data)} records into the collection '{collection_name}'.")

# def query_milvus(query_embedding, User_id, limit=5):
#     collection_name = get_collection_name(User_id)
#     # Ensure the query_embedding is a list of floats
#     if not isinstance(query_embedding, np.ndarray):
#         query_embedding = np.array(query_embedding, dtype=float)
#     else:
#         query_embedding = query_embedding.astype(float)
    
#     # Wrap the embedding in a list if it's not already
#     query_embedding = query_embedding.tolist()
#     if not client.has_collection(collection_name=collection_name):
#         create_milvus_collection(User_id, dimension=1536)
    
#     # search_res = client.search(
#     #     collection_name=collection_name,
#     #     data=query_embedding,
#     #     limit=limit,
#     #     output_fields=["text", "subject"]
#     # )
#     search_res = retry_operation(client.search,
#                                 collection_name=collection_name,
#                                 data=query_embedding,
#                                 limit=limit,
#                                 output_fields=["text", "subject"])
#     # print(search_res, type(search_res))
   
#     ## similarity threshold (close to 0, more similar it is - over 0.02 seems irrelevant)
#     threshold_dist = 0.02
#     passes_threshold = True

#     for data in search_res[0]:
#         if data.get('distance') > threshold_dist:
#             passes_threshold = False
#             break
#     return search_res, passes_threshold
