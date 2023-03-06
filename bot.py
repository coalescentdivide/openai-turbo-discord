import discord
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv
from colorama import Fore, Back, Style
import json
import tiktoken

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")
allowed_channels = os.getenv("ALLOWED_CHANNELS").split(",")
ignored_ids = os.getenv("IGNORED_IDS").split(",")
bot = commands.Bot(command_prefix='', intents=discord.Intents.all())
initial_messages = json.loads(os.getenv("INITIAL_MESSAGES"))
messages = initial_messages.copy()
max_tokens= int(os.getenv("MAX_TOKENS"))

def num_tokens_from_message(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":  # if there's a name, the role is omitted
                    num_tokens += -1  # role is always required and always 1 token
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not presently implemented for model {model}.
See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    
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
    async with message.channel.typing():
        try:
            messages.append({"role": "user", "content": message.content})
            remaining_tokens = max_tokens - num_tokens_from_message(messages)
            response = openai.ChatCompletion.create(
                model= "gpt-3.5-turbo-0301",
                messages=messages,
                max_tokens=remaining_tokens + 500,
                temperature= float(os.getenv("TEMPERATURE")),
                frequency_penalty= float(os.getenv("FREQUENCY_PENALTY")),
                presence_penalty= float(os.getenv("PRESENCE_PENALTY"))
                )            
            content = response['choices'][0]['message']['content']
            messages.append({"role": "assistant", "content": content})   
            completion_tokens = response['usage']['completion_tokens']
            prompt_tokens = response['usage']['prompt_tokens']
            total_tokens = response['usage']['total_tokens']
            if remaining_tokens < 500:
                messages = messages[len(messages) // 2:]
                print(f'{Style.DIM}Approaching token limit. Forgetting older messages...')
            print(f'{Style.DIM}{Fore.RED}{Back.WHITE}{message.author}: {Fore.BLACK}{message.content}{Style.RESET_ALL}')
            print(f'{Fore.GREEN}{Back.WHITE}{bot.user}: {Fore.BLACK}{content}{Style.RESET_ALL}')
            print(f'{Style.BRIGHT}{Fore.CYAN}Completion tokens:{completion_tokens}{Style.RESET_ALL}')
            print(f'{Style.BRIGHT}{Fore.BLUE}Prompt tokens:{prompt_tokens}{Style.RESET_ALL}')
            print(f'{Style.BRIGHT}{Fore.GREEN}Total tokens:{total_tokens}{Style.RESET_ALL}')
            #print(f'Remaining tokens:{remaining_tokens}')
            
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
