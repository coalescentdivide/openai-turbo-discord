# openai-turbo-discord
A discord bot to interact with the openai chat completions api (designed for gpt-3.5-turbo - will work with gpt4 but will be very expensive!)

* Retains trailing memory of the conversation with a dynamic self adjusting token limit.
* Can be in multiple channels with their own memories and behaviors.
* Can speak to the bot outside an allowed channel with a mention. When done this way, gets a unique memory tied to the user that mentioned. Forgets a mention convo after 5 minutes.
* Type `help` to get a list of available commands, including the ability to write, save, and load instructions directly within Discord!
* The behavior commands can be set to usable by everyone, or by authorized users only.

## Setup Guide (Windows)

### 1. Clone the repository or download and extract the zip file.

### 2. Copy the .env.example file and rename it to .env.

### 3. Obtain your Discord Bot token
###### 1. Create your bot at https://discord.com/developers/applications
###### 2. Go to the Bot tab and click "Add Bot" and give it a name.
###### 3. Click "Reset Token" to get your Discord Bot Token for the .env file.
###### 4. Disable "Public Bot".
###### 5. Enable "Message Content Intent" under "Privileged Gateway Intents".
###### 6. Go to the OAuth2 tab and select URL generator. Under Scopes check `bot`, then in the permissions check `Send Messages` and `Embed Links`. Use the generated URL to invite the bot to your server. (Designed to run on a single server)

### 4. Create or login to your OpenAI account and generate an API key at https://beta.openai.com/account/api-keys

### 5. Edit .env file and add your Discord bot token, OpenAI API key, and at least one channel for it to work in. 
###### You can find the IDs for Channels and Users by turning on Developer Mode in Discord (Settings > Appearance > Advanced) and right-clicking on the channel and selecting 'copy ID'.

### 6. Open a terminal window in the folder containing the downloaded files, and type `run.bat`. (You may have to type `./run.bat` due to powershell permissions). To shut down press `Ctrl + c`.

