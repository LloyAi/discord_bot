from flask import Flask, request, jsonify
from utils import process_files_and_get_response
from db import connect_to_rds
from main2 import milvus_handler

db_connection = connect_to_rds()

bot_api = Flask(__name__)

@bot_api.route("/ask", methods=["POST"])
def ask_discord_bot():
    """
    API endpoint to interact with the Discord bot.
    """
    data = request.get_json()
    user_message = data.get("message", "")
    username = data.get("username", "")
    user_id = data.get("user_id", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # process_files_and_get_response(user_message, user_id, username, db_connection)
    response = process_files_and_get_response(user_message, user_id, username, db_connection, milvus_handler)                               
    # # Run the async function in the event loop
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # response = loop.run_until_complete(process_files_and_get_response(user_message, user_id, username, db_connection))

    # Simulate processing (replace this with real interaction logic)
    # response = f"Hello, {username}! You said: {user_message}"
    return jsonify({"response": response})

if __name__ == "__main__":
    bot_api.run(host="0.0.0.0", port=9000)
