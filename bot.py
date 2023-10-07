import discord
from dotenv import load_dotenv
import os
import pickle
import openai
import openai_utils
import tiktoken
import sys


load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Bot(intents=intents)

guild_configurations = {}

if len(sys.argv) == 2:
    ai = openai_utils.openai_utils(model=sys.argv[1])
else:
    ai = openai_utils.openai_utils()

try:
    with open("guild_configurations.pkl", "rb") as file:
        guild_configurations = pickle.load(file)
except FileNotFoundError:
    pass


def save_guild_configurations():
    with open("guild_configurations.pkl", "wb+") as file:
        pickle.dump(guild_configurations, file)


encoding = tiktoken.encoding_for_model(ai.model)


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print(
        f"message received: {message.content} by {message.author.name}, {message.channel.category_id}, {message.guild.id}"
    )

    if message.guild.id not in guild_configurations:
        await message.channel.send(
            f"guild not initialized, use /initialize help to learn how to initialize"
        )
        return

    if message.channel.category_id != guild_configurations[message.guild.id]:
        return

    if message.content == "":
        return

    messages = []

    # set guidance for ChatGPT
    guidance = 'If sending code, wrap code with triple backticks. To specify the language, include the language name after the first set of backticks. For example, to send python code, use ```python. If the conversation does not necessarily need a response (example: responding to interjections) or is part of a conversation that doesn\'t include you, respond with "No response".'

    total_message_token = num_tokens_from_string(guidance) + num_tokens_from_string(
        f"user {message.author.name} wrote: {message.content}"
    )

    # get messages from channel
    async for channel_message in message.channel.history(limit=40):
        if channel_message.content == "":
            continue
        message_token = num_tokens_from_string(channel_message.content)
        if channel_message.author == bot.user:
            if (total_message_token + message_token) > 4097 - total_message_token:
                break
            messages.insert(
                0, {"role": "assistant", "content": channel_message.content}
            )
            total_message_token += message_token
        else:
            if (total_message_token + message_token) > 4097 - total_message_token:
                break
            messages.insert(0, {"role": "user", "content": channel_message.content})
            total_message_token += message_token

    messages.insert(0, {"role": "system", "content": guidance})

    # add user message
    messages.append(
        {
            "role": "user",
            "content": f"user {message.author.name} wrote: {message.content}",
        }
    )

    # get response from GPT
    async with message.channel.typing():
        global ai

        tries = 0

        while True:
            try:
                response = ai.get_gpt_response(messages)
                break
            except openai.error.OpenAIError as e:
                print(str(e))
                ai = openai_utils.openai_utils(model="gpt-4")
                tries += 1

            if tries > 3:
                await message.channel.send("An error occured, please try again later")
                return

        # make sure response is within discord's 2000 character limit
        if len(response) > 2000:
            # if it is over, split it into multiple messages without splitting any words
            split_responses = response.split(" ")
            current_response = ""
            for split_response in split_responses:
                if len(current_response) + len(split_response) > 1997:
                    # if it is splitting in the middle of a code block, it should add the closing backticks
                    if current_response.count("```") % 2 == 1:
                        current_response += "```"

                        await message.channel.send(current_response)
                        current_response = "```"
                    else:
                        await message.channel.send(current_response)
                        current_response = ""
                current_response += split_response + " "

            if current_response != "":
                await message.channel.send(current_response)
        else:
            await message.channel.send(response)


async def check_initialized(ctx):
    if ctx.guild.id not in guild_configurations:
        await ctx.respond("This guild is not initialized")
        return False
    return True


initialize = discord.SlashCommandGroup(
    "initialize",
    "Initializes the bot to a category",
    guild_ids=["507778138374275072", "700194499309207632", "1041571606671147069"],
)


@initialize.command(
    name="help", description="Shows help information on how to initialize the bot"
)
async def init_help(
    ctx,
):
    help_text = """
    This bot creates new channels as new chats with the ai
    
    For this bot to work well, it is recommended to create a dedicated category for the bot
    
    To initialize the bot to that category, create a channel within that category and type /initialize

    To change what category the bot is initialized to, type /initialize in a channel within the new category
    """
    embed = discord.Embed(title="Initialising information", description=help_text)
    await ctx.respond(embed=embed)
    return


@initialize.command(name="here", description="Initializes the bot to the category")
async def initialize_bot(ctx):
    if (
        ctx.guild.id in guild_configurations
        and ctx.channel.category_id == guild_configurations[ctx.guild.id]
    ):
        await ctx.respond("This catergory is already initialized")
        return

    guild_configurations[ctx.guild.id] = ctx.channel.category_id
    save_guild_configurations()
    await ctx.respond("Initialized")


chats = discord.SlashCommandGroup(
    "chat",
    "Commands for managing chats",
    guild_ids=["507778138374275072", "700194499309207632", "1041571606671147069"],
)


@chats.command(name="new", description="Creates a new chat")
async def new_chat(ctx, name: str):
    if not await check_initialized(ctx):
        return

    category_id = guild_configurations[ctx.guild.id]
    category = discord.utils.get(ctx.guild.categories, id=category_id)
    channel = await category.create_text_channel(name)
    await ctx.respond(
        f"Created new chat {channel.mention}", delete_after=5, ephemeral=True
    )


@chats.command(name="delete", description="Deletes the current chat")
async def delete_chat(ctx):
    if not await check_initialized(ctx):
        return

    if ctx.channel.category_id != guild_configurations[ctx.guild.id]:
        await ctx.respond("This channel is not a chat channel")
        return
    await ctx.respond(f"Deleting chat {ctx.channel.mention}")
    await ctx.channel.delete()


@chats.command(name="here", description="Respond in this current chat")
async def here_chat(ctx, prompt: str):
    messages = []

    # set guidance for ChatGPT
    guidance = "If sending code, wrap code with triple backticks. To specify the language, include the language name after the first set of backticks. For example, to send python code, use ```python. Give detailed summaries for answers for more factual questions."

    total_message_token = num_tokens_from_string(guidance) + num_tokens_from_string(
        f"user {ctx.author.name} wrote: {prompt}"
    )

    # get messages from channel
    async for channel_message in ctx.channel.history(limit=10):
        if channel_message.content == "":
            continue
        message_token = num_tokens_from_string(channel_message.content)
        if channel_message.author == bot.user:
            if (total_message_token + message_token) > 4097 - total_message_token:
                break
            messages.insert(
                0, {"role": "assistant", "content": channel_message.content}
            )
            total_message_token += message_token
        else:
            if (total_message_token + message_token) > 4097 - total_message_token:
                break
            messages.insert(0, {"role": "user", "content": channel_message.content})
            total_message_token += message_token

    messages.insert(0, {"role": "system", "content": guidance})

    # add user message
    messages.append(
        {"role": "user", "content": f"user {ctx.author.name} wrote: {prompt}"}
    )

    # get response from GPT
    async with ctx.channel.typing():
        try:
            response = ai.get_gpt_response(messages)
        except openai.error.OpenAIError as e:
            print(str(e))
            await ctx.respond(
                "An error occured, please try again later", ephemeral=True
            )
            return

        await ctx.respond("Answering", ephemeral=True)

        # make sure response is within discord's 2000 character limit
        if len(response) > 2000:
            # if it is over, split it into multiple messages without splitting any words
            split_responses = response.split(" ")
            current_response = ""
            for split_response in split_responses:
                if len(current_response) + len(split_response) > 1997:
                    # if it is splitting in the middle of a code block, it should add the closing backticks
                    if current_response.count("```") % 2 == 1:
                        current_response += "```"

                    await ctx.channel.send(current_response)
                    current_response = ""
                current_response += split_response + " "

            if current_response != "":
                await ctx.channel.send(current_response)
        else:
            await ctx.channel.send(response)

    await ctx.respond("Done", ephemeral=True)


imaging = discord.SlashCommandGroup(
    "image",
    "Create or edit images using DALL-E",
    guild_ids=["507778138374275072", "700194499309207632", "1041571606671147069"],
)


@imaging.command(name="create", description="Creates an image using DALL-E")
async def create_image(ctx, prompt: str):
    if not await check_initialized(ctx):
        return

    await ctx.defer()
    try:
        response = ai.create_image_with_prompt(prompt)
    except openai.error.OpenAIError as e:
        print(str(e))
        await ctx.respond("An error occured, please try again later")
        return
    embed = discord.Embed(title=prompt)
    embed.set_image(url=response)
    await ctx.followup.send(embed=embed)


debug = discord.SlashCommandGroup(
    "debug", "Debug commands", guild_ids=["507778138374275072"]
)


@debug.command(name="history", description="Shows the history of the current chat")
async def history_debug(ctx):
    if not await check_initialized(ctx):
        return

    async for message in ctx.channel.history(limit=20):
        if message.content == "":
            print("No message content")
        else:
            print(message.content)
    await ctx.respond("Done", ephemeral=True)


bot.add_application_command(initialize)
bot.add_application_command(chats)
bot.add_application_command(debug)
bot.add_application_command(imaging)

bot.run(os.getenv("DISCORD_TOKEN"))
