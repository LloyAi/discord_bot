from flask import Flask, request, jsonify

bot_api = Flask(__name__)

@bot_api.route("/ask", methods=["POST"])
def ask_discord_bot():
    """
    API endpoint to interact with the Discord bot.
    """
    data = request.get_json()
    user_message = data.get("message", "")
    username = data.get("username", "")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # Simulate processing (replace this with real interaction logic)
    response = f"Hello, {username}! You said: {user_message}"
    return jsonify({"response": response})

if __name__ == "__main__":
    bot_api.run(host="0.0.0.0", port=9000)
