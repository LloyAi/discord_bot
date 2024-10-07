Here’s the updated `README.md` file with all the `pip` installs included:

---

# Discord AI Bot

## Introduction

Welcome to the Discord AI Bot repository! This bot is designed to interact with users on Discord, providing various functionalities driven by AI. Follow the instructions below to set up and run your bot.

## Installation

### Prerequisites

Make sure you have Python installed (preferably version 3.8+).

### Steps

1. Install the required packages:

   ```sh
   pip install discord
   pip install python-dotenv
   pip install tiktoken
   pip install numpy
   pip install openai
   pip install pdfplumber
   pip install python-docx
   pip install pymilvus
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

2. Place your tokens and other secrets in a `.env` file. Your `.env` file should look like this:
   ```sh
   DISCORD_TOKEN=your_discord_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   DISCORD_LOG_CHANNEL_ID = your log channel id
   ```

## Running the Bot

1. Open `main.py` in your favorite code editor.
2. Run the Python code:
   ```sh
   python main.py
   ```

## Support

If you encounter any issues or have questions, please open an issue and reach out to Vishal Romel Charran.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

This version includes all the dependencies and an updated `.env` configuration based on the imports you've shared. Let me know if you need any other adjustments!
