# openai-turbo-discord
A discord bot to interact with the openai chat completions api (gpt-3.5-turbo, gpt4)

# Features

* **Memory**: Retains trailing memory of the conversation up to the set token limit. Each allowed channel now has its own memory!
* **Discord Character Limit**: Splits responses to ensure they fit within Discord's 2000 character limit
* **Behavior**: Swappable instructions via text files
* **Commands**: type `help` to get a list of the commands. Can write, save and load instructions from within discord!

# Setup

## OpenAI and Discord bot setup
1. Create or login to your openai account and generate an API key `https://platform.openai.com/account/api-keys` (you will need this key for step 3 in Installation!)  
2. Create your own Discord bot at `https://discord.com/developers/applications`
3. Go to the Bot tab and click "Add Bot"
4. Click "Reset Token" and copy your Discord bot token (you will need this token for step 3 in Installation!) and Disable "Public Bot"
5. Enable "Message Content Intent" under "Privileged Gateway Intents"
6. Go to the OAuth2 tab and select URL generator. Under Scopes check `bot`, then in the permissions check `Send Messages` and `Embed Links`. Use the generated URL to invite the bot to your server.

## Installation 
note: This guide assumes you have python installed on your system (3.9 or 3.10 recommended)
1. Clone the repository or download and extract the zip file.
2. Copy the .env.example file and rename it to .env.
3. Edit .env file and add your Discord bot token, OpenAI API key, and at least one channel for it to work in.
4. Open a terminal window and navigate to the folder containing the downloaded files, then type run.bat. To shut down press `Ctrl + c`
