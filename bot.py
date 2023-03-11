import discord
from discord.ext import commands
import openai
import os
from dotenv import load_dotenv
from colorama import Fore, Back, Style
import tiktoken
import json

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")
allowed_channels = os.getenv("ALLOWED_CHANNELS").split(",")
ignored_ids = os.getenv("IGNORED_IDS").split(",")
bot = commands.Bot(command_prefix='', intents=discord.Intents.all())
max_tokens= 3500

def list_prompts():
    """Lists prompt filenames in "./prompts" directory with ".txt" extension, removes extension, and returns modified names"""    
    behavior_files = []
    for filename in os.listdir("./prompts"):
        if filename.endswith(".txt"):
            behavior_files.append(os.path.splitext(filename)[0])
    return behavior_files

def load_prompt(filename):
    """Loads a prompt from a file, processes it, and returns JSON data as a Python object."""   
    if not filename.endswith(".txt"):
        filename += ".txt"
    with open(f"./prompts/{filename}", encoding="utf-8") as file:
        lines = file.readlines()
    return json.loads(build_convo(lines))

def save_convo(convo, filename):
    """Write a conversation to a text file."""
    with open(filename, "w") as file:
        for line in convo:
            role = line["role"]
            content = line["content"]
            file.write(f"{role}: {content}\n")

def de_json(convo):
    """Convert a conversation from JSON to human-readable text."""
    conversation = []
    for message in convo:
        role = message['role']
        content = message['content']
        conversation.append(f"{role}: {content}")
    return "\n".join(conversation)

def build_convo(lines):
    """Converts a conversation in text format to JSON format."""
    conversation = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(': ')
        if len(parts) >= 2:
            role = parts[0]
            content = parts[1]
        else:
            role = "user"
            content = line
        conversation.append({"role": role, "content": content})
    return json.dumps(conversation)

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
    print(f'{Fore.GREEN}Logged in as {bot.user}{Style.RESET_ALL}')
    filename = os.getenv('DEFAULT_PROMPT')  # set the default behavior file
    global messages
    messages = load_prompt(filename)
@bot.event
async def on_message(message):
    global messages
    filename = os.getenv('DEFAULT_PROMPT')
    if message.author.bot or message.author.id in ignored_ids:
        return
    if str(message.channel.id) not in allowed_channels:
        return
    if message.reference is not None:  # ignore replies
        return
    if message.content.startswith('!'):
        return
    
    if message.content == "help":
        embed = discord.Embed(title="Commands", color=0x00ff00)
        embed.add_field(name="wipe memory", value="Wipes the chatbot's memory and loads the default behavior", inline=False)
        embed.add_field(name="new behavior", value="Allows the user to manually write a new behavior for the chatbot", inline=False)
        embed.add_field(name="save behavior", value="Saves the current conversation memory as a new behavior", inline=False)
        embed.add_field(name="load behavior", value="Loads a saved behavior", inline=False)
        await message.channel.send(embed=embed)
        return
        
    if message.content == "wipe memory":
        messages.clear()
        messages = load_prompt(filename)
        await message.channel.send("Memory wiped!")
        print(f'{Fore.RED}Memory Wiped{Style.RESET_ALL}')
        return
    
    if message.content == "new behavior":
        messages.clear()
        await message.channel.send("Write the base conversation:")
        def check(msg):
            return msg.author == message.author and msg.channel == message.channel
        msg = await bot.wait_for("message", check=check)
        messages = json.loads(build_convo(msg.content.strip().split('\n')))
        async for m in message.channel.history(limit=1):
            if m.author == message.author and m.content:
                last_user_message = m.content
                break
        embed = discord.Embed(title="New behavior Set!", description=last_user_message, color=0x00ff00)
        await message.channel.send(embed=embed)
        return
    
    if message.content == "save behavior":
        await message.channel.send("Name your new behavior:")
        def check(msg):
            return msg.author == message.author and msg.channel == message.channel
        msg = await bot.wait_for("message", check=check)
        filename = "prompts/" + msg.content.strip() + ".txt"
        convo_str = de_json(messages)
        with open(filename, "w") as file:
            file.write(convo_str)
            print(f'{Fore.RED}Behavior Saved:\n{Style.DIM}{Fore.GREEN}{Back.WHITE}{de_json(messages)}{Style.RESET_ALL}')
        await message.channel.send(f"Behavior saved as {filename}")
    
    if message.content == "load behavior":
        behavior_files = list_prompts()
        if behavior_files:
            behavior_files_str = "\n".join(behavior_files)
            embed = discord.Embed(title="Which behavior to load?", description=behavior_files_str)
            await message.channel.send(embed=embed)
            def check(msg):
                return msg.author == message.author and msg.channel == message.channel
            msg = await bot.wait_for("message", check=check)
            filename = msg.content.strip()
            if filename in behavior_files:
                conversation = load_prompt(filename)
                os.environ["DEFAULT_PROMPT"] = filename
                messages.clear()
                messages = load_prompt(filename)                
                convo_str = de_json(conversation)
                embed = discord.Embed(title=f"Behavior loaded: {filename}", description=convo_str, color=0x00ff00)
                print(f'{Fore.RED}Behavior Loaded:\n{Style.DIM}{Fore.GREEN}{Back.WHITE}{de_json(messages)}{Style.RESET_ALL}')
                await message.channel.send(embed=embed)
            else:
                await message.channel.send(f"File not found: {filename}")
        else:
            await message.channel.send("No behavior files found.")
        return
    if message.content != filename:
        
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
                #print(f'{messages}')
                #print(f'Remaining tokens:{remaining_tokens}\nCurrent Memory:\n{messages}')
                
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
