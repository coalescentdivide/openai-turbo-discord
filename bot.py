import asyncio
from colorama import Fore, Back, Style
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import openai
import os
import tiktoken

load_dotenv()
openai.api_key = os.getenv("OPENAI_KEY")
allowed_channels = os.getenv("ALLOWED_CHANNELS").split(",")
ignored_ids = os.getenv("IGNORED_IDS").split(",")
bot = commands.Bot(command_prefix='', intents=discord.Intents.all())
allow_commands = os.getenv("ALLOW_COMMANDS").lower() == "true"
admin_id = os.getenv("ADMIN_IDS").split(",")
current_behavior_filename = os.getenv('DEFAULT_PROMPT')
temperature = float(os.getenv("TEMPERATURE"))
frequency_penalty = float(os.getenv("FREQUENCY_PENALTY"))
presence_penalty = float(os.getenv("PRESENCE_PENALTY"))
top_p = float(os.getenv("TOP_P"))

channel_messages = {}
responses = {}
command_mode_flag = {}
message_queue_locks = {}

def allowed_command(user_id):
    if str(user_id) in admin_id:
        return True
    elif allow_commands:
        return True
    else:
        return False

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

def save_convo(messages, filename, channel_id):
    """Saves the current memory to a text file"""
    convo_str = de_json(messages)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(convo_str)
        print(f'{Fore.RED}Behavior Saved:\n{Style.DIM}{Fore.GREEN}{Back.WHITE}{convo_str}{Style.RESET_ALL}')
    return f"Behavior saved as `{os.path.splitext(os.path.basename(filename))[0]}`"

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
    role = "user"
    content = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(':', maxsplit=1)
        if len(parts) >= 2:
            if content:
                conversation.append({"role": role, "content": content})
                content = ""
            role = parts[0]
            content = parts[1].strip()
        else:
            content += "\n" + line if content else line
    if content:
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
    
async def get_chat_response(messages, max_tokens):
    """Returns the response object from OpenAI's Chat API"""
    response = await asyncio.to_thread(
        openai.ChatCompletion.create,
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max_tokens,
        top_p=top_p,
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )
    return response

async def chat_response(messages):
    """Wrapper function for memory management"""
    max_tokens = int(os.getenv("MAX_TOKENS"))
    num_tokens = num_tokens_from_message(messages)
    remaining_tokens = max_tokens - num_tokens
    current_behavior = load_prompt(current_behavior_filename)
    if isinstance(current_behavior, list):
        behavior_len = len(current_behavior)
    else:
        behavior_len = 1
    start_index = behavior_len
    while remaining_tokens / max_tokens < 0.2 and len(messages) > behavior_len:
        oldest_tokens = num_tokens_from_message(messages[start_index:start_index+1])
        messages = messages[:start_index] + messages[start_index+1:]
        num_tokens -= oldest_tokens
        remaining_tokens = max_tokens - num_tokens
    if remaining_tokens / max_tokens >= 0.2:
        response = await get_chat_response(messages, remaining_tokens)
        completion_tokens = response['usage']['completion_tokens']
        prompt_tokens = response['usage']['prompt_tokens']
        total_tokens = response['usage']['total_tokens']
        print(f'{Style.BRIGHT}{Fore.CYAN}Completion tokens:{completion_tokens}{Style.RESET_ALL}\n{Style.BRIGHT}{Fore.BLUE}Prompt tokens:{prompt_tokens}{Style.RESET_ALL}\n{Style.BRIGHT}{Fore.GREEN}Total tokens:{total_tokens}{Style.RESET_ALL}')
        remaining_tokens -= completion_tokens
        print(f'{Style.DIM}{Fore.WHITE}Remaining tokens:{remaining_tokens}{Style.RESET_ALL}')
    #print(f'Current Memory:{messages}')
    return response

async def discord_chunker(message, content):
    """Splits text into multiple messages if length is over discord character limit"""
    if len(content) <= 1950:
        await message.channel.send(content)
    else:
        chunks = []
        while len(content) > 1950:
            paragraph_end_index = content.rfind('\n\n', 0, 1950)
            if paragraph_end_index != -1:
                chunks.append(content[:paragraph_end_index+1] + '\u200b' + '\n')
                content = content[paragraph_end_index+2:]
            else:
                newline_end_index = content.rfind('\n', 0, 1950)
                if newline_end_index != -1:
                    chunks.append(content[:newline_end_index+1])
                    content = content[newline_end_index+1:]
                else:
                    sentence_end_index = content.rfind('. ', 0, 1950)
                    if sentence_end_index != -1:
                        chunks.append(content[:sentence_end_index+1])
                        content = content[sentence_end_index+2:]
                    else:
                        word_end_index = content.rfind(' ', 0, 1950)
                        chunks.append(content[:word_end_index])
                        content = content[word_end_index+1:]
        chunks.append(content)
        for chunk in chunks:
            await message.channel.send(chunk)

@bot.event
async def on_ready():
    print(f'{Fore.GREEN}Logged in as {bot.user}{Style.RESET_ALL}')

async def forget_mentions(user_channel_key):
    await asyncio.sleep(300)
    if user_channel_key in channel_messages:
        del channel_messages[user_channel_key]
        print(f'{Fore.RED}Forgetting side convo with user {user_channel_key}{Style.RESET_ALL}')

@bot.event
async def on_message(message):
    global current_behavior_filename

    await asyncio.sleep(0.1)
    if message.author.bot or message.author.id in ignored_ids:
        return
    bot_mentioned_in_unallowed_channel = str(message.channel.id) not in allowed_channels and bot.user in message.mentions
    if not bot_mentioned_in_unallowed_channel and str(message.channel.id) not in allowed_channels:
        return
    message_content = message.content.replace(f'{bot.user.mention} ', '') if message.content.startswith(f'{bot.user.mention} ') else message.content
    if message.reference is not None or message.content.startswith('!'):
        return
    
    def check(msg):
        return msg.author == message.author and msg.channel == message.channel

    if message.content.lower() == "help":
        embed = discord.Embed(title=f"Send a message in this channel to get a response from {message.guild.me.nick}\nReplies to other users or messages that start with ! are ignored", color=0x00ff00)
        embed.add_field(name="wipe memory", value=f"Wipes the short-term memory and reloads the current behavior", inline=False)
        embed.add_field(name="new behavior", value=f"Allows the user to set a new behavior to the current memory", inline=False)
        embed.add_field(name="save behavior", value=f"Saves the current memory as a behavior template", inline=False)
        embed.add_field(name="load behavior [behavior name]", value=f"Wipes memory and loads the specified behavior template. If no filename is provided, a list of available behavior templates will be shown. Then respond with the name of the template you wish to load.", inline=False)
        embed.add_field(name="reset", value=f"Wipes memory and loads the default behavior", inline=False)
        embed.add_field(name="@mention", value=f"You can also mention {message.guild.me.nick} outside of this channel. Keep mentioning it to continue that conversation, otherwise a mention convo is erased automatically after 5 minutes", inline=False)
        await message.channel.send(embed=embed)
        return

    elif message.content.lower() == "wipe memory":
        channel_messages[message.channel.id].clear()
        channel_messages[message.channel.id] = load_prompt(current_behavior_filename)
        await message.channel.send(f"Memory wiped! Current Behavior is `{os.path.splitext(os.path.basename(current_behavior_filename))[0]}`")
        print(f'{Fore.RED}Memory Wiped{Style.RESET_ALL}')
        return

    elif message.content.lower() == "reset":
        if not allowed_command(message.author.id):
            await message.channel.send("You are not allowed to use this command.")
            return      
        channel_messages[message.channel.id].clear()
        channel_messages[message.channel.id] = load_prompt(filename=os.getenv('DEFAULT_PROMPT'))
        current_behavior_filename = os.getenv('DEFAULT_PROMPT')
        await message.channel.send(f"Reset to `{os.path.splitext(os.path.basename(current_behavior_filename))[0]}`!")
        print(f'{Fore.RED}Reset!{Style.RESET_ALL}')
        return

    elif message.content.lower() == "new behavior":
        if not allowed_command(message.author.id):
            await message.channel.send("You are not allowed to use this command.")
            return 
        command_mode_flag[message.channel.id] = True
        channel_messages[message.channel.id] = []
        embed = discord.Embed(title=f"Write the new behavior", description=(f'Provide a new behavior. Can be a single prompt, or you can provide an example conversation in the following format:\n\nsystem: a system message\nuser: user message 1\nassistant: example response 1\nuser: user message 2\nassistant: example response 2\n\n'), color=0x00ff00)        
        embed.set_footer(text=(f'If you wish to recall your new behavior later, don\'t forget to save it by typing `save behavior`'))
        await message.channel.send(embed=embed)
        msg = await bot.wait_for("message", check=check)
        channel_messages[message.channel.id] = json.loads(build_convo(msg.content.strip().split('\n')))
        async for m in message.channel.history(limit=1):
            if m.author == message.author and m.content:
                last_user_message = m.content
                break
        embed = discord.Embed(title="New behavior Set!", description=last_user_message, color=0x00ff00)
        await message.channel.send(embed=embed)
        return

    elif message.content.lower() == "save behavior":
        if not allowed_command(message.author.id):
            await message.channel.send("You are not allowed to use this command.")
            return 
        command_mode_flag[message.channel.id] = True
        await message.channel.send("Name your behavior:")
        msg = await bot.wait_for("message", check=check)
        filename = "prompts/" + msg.content.strip() + ".txt"
        messages = channel_messages[message.channel.id]
        await message.channel.send(save_convo(messages, filename, message.channel.id))

    elif message.content.lower().startswith("load behavior"):
        if not allowed_command(message.author.id):
            await message.channel.send("You are not allowed to use this command.")
            return 
        behavior_files = list_prompts()
        if not behavior_files:
            await message.channel.send("No behavior files found.")
            return
        command_len = len("load behavior")
        if len(message.content) > command_len:
            filename = message.content[command_len:].strip().lower()
            if filename not in [f.lower() for f in behavior_files]:
                await message.channel.send(f"File not found: {filename}")
                return
        else:
            command_mode_flag[message.channel.id] = True
            behavior_files_str = "\n".join(behavior_files)
            embed = discord.Embed(title="Which behavior to load?", description=behavior_files_str)
            await message.channel.send(embed=embed)
            msg = await bot.wait_for("message", check=check)
            filename = msg.content.strip().lower()
            if filename not in behavior_files:
                await message.channel.send(f"File not found: {filename}")
                return
        behavior = load_prompt(filename)
        channel_messages[message.channel.id] = behavior
        convo_str = de_json(behavior)
        current_behavior_filename = filename
        embed = discord.Embed(title=f"Behavior loaded: {filename}", description="", color=0x00ff00)
        await message.channel.send(embed=embed)
        await discord_chunker(message, convo_str)
        print(f'{Fore.RED}Behavior Loaded:\n{Style.DIM}{Fore.GREEN}{Back.WHITE}{convo_str}{Style.RESET_ALL}')
        return

    else:
        if bot_mentioned_in_unallowed_channel:
            user_channel_key = message.author.id
        else:
            user_channel_key = message.channel.id
        messages = channel_messages.get(user_channel_key)
        if messages is None:
            messages = load_prompt(filename=os.getenv("DEFAULT_PROMPT"))
            channel_messages[user_channel_key] = messages
        if command_mode_flag.get(message.channel.id):
            command_mode_flag[message.channel.id] = False
            return
        
        if user_channel_key not in message_queue_locks:
            message_queue_locks[user_channel_key] = asyncio.Lock()

        async with message_queue_locks[user_channel_key]:
            async with message.channel.typing():
                try:
                    messages.append({"role": "user", "content": message_content})
                    response = await chat_response(messages)
                    content = response['choices'][0]['message']['content']
                    messages.append({"role": "assistant", "content": content})
                    print(f'Channel: {message.channel.name}\n{Style.DIM}{Fore.RED}{Back.WHITE}{message.author}: {Fore.BLACK}{message_content}{Style.RESET_ALL}\n{Style.DIM}{Fore.GREEN}{Back.WHITE}{bot.user}: {Fore.BLACK}{content}{Style.RESET_ALL}')                
                    responses[message.id] = content
                    if message.id in responses:
                        response_content = responses[message.id]
                        await discord_chunker(message, response_content)
                    if bot_mentioned_in_unallowed_channel:
                        asyncio.create_task(forget_mentions(user_channel_key))
                except Exception as e:
                    print(type(e), e)
                    await message.channel.send("Sorry, there was an error processing your message.")

bot.run(os.getenv("DISCORD_TOKEN"))
