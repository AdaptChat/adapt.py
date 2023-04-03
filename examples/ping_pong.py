"""Example of a simple bot that responds to any message that says "ping" with "Pong!"."""

import adapt

client = adapt.Client()


# Ready event handler. This is called when the client is ready to start receiving events.
@adapt.once
@client.event
async def on_ready(ready):
    print(f'Ready as {ready.user}')


# Message event handler. This is called when a message is received.
@client.event
async def on_message(message):
    # Ignore messages sent by bots
    if message.author.is_bot:
        return

    # If the message content is "ping", respond with "Pong!".
    if message.content == 'ping':
        await message.channel.send('Pong!')


# Run the client with your bot token.
client.run('token')
