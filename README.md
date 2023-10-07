# ChatGPT *(and DALL-E)* on Discord

## About
A discord bot built on python with py-cord that uses the openai library.

This bot utilises categories in servers and channels as chats. By initialising the bot to a category in the server, the bot will answer every message sent in any channel in the category.

## Usage

The bot has 3 main slash commands

- **/initialise**: 
    - **/initialise help**: Sends instructions on how to initialise the bot
    - **/initialise here**: Use this command in a channel in the category you want to initialise the bot to
- **/chat**:
    - **/chat new**: Creates a new chat
    - **/chat delete**: Deletes the current chat
        - *note: this can be a bit dangerous as it will allow anyone to delete any chat in the category*
- **/image**:
    - **/image create**: Generates a 512x512 image from the given prompt

## Setting up
This bot reads from a .env file

```
DISCORD_TOKEN = discord application token
OPENAI_API_KEY = openai key
```

required packages
- py-cord
- openai
- python-dotenv
- tiktoken

*note: py-cord and discord.py uses the same name space. I'm not sure what will happen if you use discord.py instead*

## Limitations

- /chat features can be dangerous/annoying if used irresponsibly
- only the last 40 messages in a channel are recalled and used as context
- it is a pretty basic bot

## Plans

- potentially restrict usage of chat features to certain roles or admins
- Giving it the ability to choose when it responds instead of responding to every message sent