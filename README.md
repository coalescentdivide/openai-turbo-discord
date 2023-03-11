# openai-turbo-discord
A discord bot to interact with the openai chat completions api (gpt-3.5-turbo)

## Features

* **Memory**: Retains trailing memory of the conversation up to the set token limit
* **Discord Character Limit**: Splits responses to ensure they fit within Discord's 2000 character limit
* **Behavior**: Swappable instructions via text files
* **Commands**: type `help` to get a list of the commands. Can write, save and load instructions from within discord

## Installation
1. Clone the repository or download and extract the zip file.
2. Copy the .env.example file and rename it to .env.
3. Edit .env file and add your Discord bot token, OpenAI API key, and at least one channel for it to work in.
4. Can optionally edit the example_convo.txt file or make another txt file in the same format
5. Open a terminal window and navigate to the folder containing the downloaded files, then type run.bat
