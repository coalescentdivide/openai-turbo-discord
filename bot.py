import discord
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv
from colorama import Fore, Back, Style
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")
allowed_channels = os.getenv("ALLOWED_CHANNELS").split(",")
ignored_ids = os.getenv("IGNORED_IDS").split(",")
bot = commands.Bot(command_prefix='', intents=discord.Intents.all())
initial_messages = json.loads(os.getenv("INITIAL_MESSAGES"))
messages = initial_messages.copy()

@bot.event
async def on_ready():
    print(Fore.GREEN + 'Logged in as {0.user}'.format(bot) + Style.RESET_ALL)

@bot.event
async def on_message(message):
    global messages
    if message.author.bot or message.author.id in ignored_ids:
        return
    if str(message.channel.id) not in allowed_channels:
        return
    try:
        messages.append({"role": "user", "content": message.content})
        response = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo",
            messages=messages,
            max_tokens= int(os.getenv("MAX_TOKENS")),
            temperature= float(os.getenv("TEMPERATURE")),
            frequency_penalty= float(os.getenv("FREQUENCY_PENALTY")),
            presence_penalty= float(os.getenv("PRESENCE_PENALTY"))
            )            
        content = response['choices'][0]['message']['content']
        messages.append({"role": "assistant", "content": content})   
        completion_tokens = response['usage']['completion_tokens']
        prompt_tokens = response['usage']['prompt_tokens']
        total_tokens = response['usage']['total_tokens']
        if total_tokens >= int(os.getenv("MAX_TOKENS")):
            messages.pop(0)
            print(f'{Style.DIM}Token limit reached. Removed oldest message from memory')
        print(f'{Style.DIM}{Fore.RED}{Back.WHITE}{message.author}: {Fore.BLACK}{message.content}{Style.RESET_ALL}')
        print(f'{Fore.GREEN}{Back.WHITE}{bot.user}: {Fore.BLACK}{content}{Style.RESET_ALL}')
        print(f'{Style.BRIGHT}{Fore.CYAN}Completion tokens:{completion_tokens}{Style.RESET_ALL}')
        print(f'{Style.BRIGHT}{Fore.BLUE}Prompt tokens:{prompt_tokens}{Style.RESET_ALL}')
        print(f'{Style.BRIGHT}{Fore.GREEN}Total tokens:{total_tokens}{Style.RESET_ALL}')
        
        async with message.channel.typing():
            if len(content) <= 2000:
                await message.channel.send(content)
            else:
                chunks = []
                while len(content) > 2000:
                    word_end_index = content.rfind(' ', 0, 2000)
                    if word_end_index == -1:                        
                        chunks.append(content[:2000])
                        content = content[2000:]
                    else:
                        chunks.append(content[:word_end_index])
                        content = content[word_end_index+1:]
                chunks.append(' ' + content)
                for chunk in chunks:
                    await message.channel.send(chunk)

    except Exception as e:
        print(type(e), e)
        await message.channel.send("Sorry, there was an error processing your message.")

bot.run(os.getenv("DISCORD_TOKEN"))
