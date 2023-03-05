# openai-turbo-discord
A discord bot to interact with the openai chat completions api (gpt-3.5-turbo) Retains memory of the conversation up to the set token limit, then removes the oldest message in the conversation. The script also respects the Discord character limit of 2000 characters (no nitro)

## Features

* **Memory**: Retains memory of the conversation up to the set token limit, then removes the oldest message from memory
* **Discord Character Limit**: Splits responses to ensure they fit within Discord's 2000 character limit
* **Additional Control**: You can adjust other settings including the behavior/personality and other model hyperparameters with the .env file

## Installation
1. Clone the repository or download and extract the zip file.
2. Copy the .env.example file and rename it to .env.
3. Edit .env file and add your Discord bot token, OpenAI API key, and at least one channel for it to work in.
4. Update any other settings in the .env file as needed
5. Open a terminal window and navigate to the folder containing the downloaded files, then type run.bat
