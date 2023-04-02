# adapt.py
Official wrapper around Adapt's API for Python.

## Installation
```bash
pip install adapt.py
```

From GitHub:
```bash
pip install git+https://github.com/AdaptChat/adapt.py
```

## Usage
```python
import adapt

class Client(adapt.Client):
    """My example client"""

    @adapt.once  # This event will only be called once
    async def on_ready(self, ready: adapt.ReadyEvent) -> None:
        print(f"Logged in as {ready.user}!")

    async def on_message(self, message: adapt.Message) -> None:
        if message.content == "!ping":
            await message.channel.send("Pong!")

if __name__ == "__main__":
    client = Client()
    client.run("token")
```

## Using adapt.py with a custom Adapt instance
Adapt.py defaults to use the official Adapt instance at https://adapt.chat. If you want to use a custom instance,
pass an `AdaptServer` instance to the `server` kwarg when constructing the client.

`AdaptServer.local()` can be used as a shortcut to create a server instance for a local instance of Adapt:

```python
from adapt import AdaptServer, Client

client = Client(server=AdaptServer.local())  # Use a local instance of Adapt
...
```

Or, you can manually pass in URLs:
```python
from adapt import AdaptServer, Client

server = AdaptServer(
    api="https://my-adapt-instance.com/api",
    harmony="https://my-adapt-instance.com/harmony",
    convey="https://my-adapt-instance.com/convey",
)
client = Client(server=server)
...
```
